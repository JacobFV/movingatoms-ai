"""The site's processing-worker API (/app/api/worker/*, bearer WORKER_TOKEN). See README "Processing" and
docs/INTERNAL.md. Every helper raises ApiError on a non-2xx answer."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests

PART = 64 * 1024 * 1024  # multipart part size for uploads (the Worker body limit is 100 MB)
PART_DL = 16 * 1024 * 1024  # ranged-read size for parallel downloads
SINGLE_MAX = 90 * 1024 * 1024


class ApiError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"{status}: {body[:500]}")
        self.status = status
        self.body = body


@dataclass
class Api:
    base: str  # https://movingatoms-ai.pages.dev
    token: str

    @classmethod
    def from_env(cls) -> "Api":
        return cls(os.environ.get("MA_SITE", "https://movingatoms-ai.pages.dev").rstrip("/"), os.environ["WORKER_TOKEN"])

    # ---------- plumbing ----------
    def _url(self, path: str) -> str:
        return f"{self.base}/app/api/worker{path}"

    def _req(self, method: str, path: str, *, retries: int = 4, **kw: Any) -> requests.Response:
        headers = {"Authorization": f"Bearer {self.token}", **kw.pop("headers", {})}
        for attempt in range(retries + 1):
            try:
                r = requests.request(method, self._url(path), headers=headers, timeout=kw.pop("timeout", 300), **kw)
            except requests.RequestException:
                if attempt == retries:
                    raise
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code >= 500 and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code >= 400:
                raise ApiError(r.status_code, r.text)
            return r
        raise AssertionError("unreachable")

    def _json(self, method: str, path: str, body: Any | None = None, **kw: Any) -> Any:
        r = self._req(method, path, json=body, **kw)
        return r.json() if r.content else None

    # ---------- jobs ----------
    def claim(self, types: Iterable[str] | None = None, worker: str | None = None, max_size: int | None = None) -> dict | None:
        """The oldest queued job of these types; `max_size` skips jobs whose input.size (source bytes) is larger."""
        body: dict[str, Any] = {"types": list(types or []), "worker": worker or os.environ.get("MA_WORKER_NAME") or os.uname().nodename}
        if max_size:
            body["max_size"] = int(max_size)
        r = self._req("POST", "/jobs/claim", json=body)
        return None if r.status_code == 204 else r.json()

    def job(self, job_id: str, **fields: Any) -> None:
        """status, stage, progress (0..1), result, error"""
        self._json("PATCH", f"/jobs/{job_id}", fields)

    # ---------- project data ----------
    def project(self, pid: str) -> dict:
        return self._json("GET", f"/projects/{pid}")

    def scan(self, scan_id: str, **fields: Any) -> dict:
        """status, stage_detail, progress, point_count, bounds, frame, labels, overview, brief, viewer, potree_prefix,
        copc_key, error. status='ready' activates the project, prices the estimate and starts the agent."""
        return self._json("PATCH", f"/scans/{scan_id}", fields)["scan"]

    def add_file(self, pid: str, r2_key: str, *, kind: str = "deliverable", name: str | None = None,
                 content_type: str | None = None, meta: dict | None = None) -> dict:
        return self._json("POST", f"/projects/{pid}/files", {"r2_key": r2_key, "kind": kind, "name": name,
                                                               "content_type": content_type, "meta": meta})["file"]

    def update_file(self, file_id: str, **fields: Any) -> dict:
        """Update a project file row: status ('ready' | 'failed'), size_bytes, content_type."""
        return self._json("POST", f"/files/{file_id}", fields)

    def release(self, job_id: str) -> None:
        """Put a claimed job back in the queue (too big for this machine, or this worker is shutting down)."""
        self._json("POST", f"/jobs/{job_id}/release", {})

    def add_revision(self, pid: str, **fields: Any) -> dict:
        """title, notes, status, model_seq, graph_key, glb_key, view_key, ifc_key, heatmap, heatmaps, renders"""
        return self._json("POST", f"/projects/{pid}/revisions", fields)["revision"]

    def update_revision(self, pid: str, number: int, **fields: Any) -> dict:
        return self._json("PATCH", f"/projects/{pid}/revisions/{number}", fields)["revision"]

    def set_estimate(self, pid: str, estimate: dict) -> dict:
        return self._json("PUT", f"/projects/{pid}/estimate", estimate)["estimate"]

    def message(self, pid: str, text: str, *, role: str = "system", body: dict | None = None) -> dict:
        return self._json("POST", f"/projects/{pid}/messages", {"role": role, "body": body or {"text": text}})["message"]

    def events(self, pid: str, *events: dict) -> None:
        self._json("POST", f"/projects/{pid}/events", {"events": list(events)})

    def set_live_heatmap(self, pid: str, scan_id: str, entry: dict) -> dict:
        """The live model's heatmap for a scan (served as the viewer manifest's live_heatmaps[scan_id])."""
        return self._json("PUT", f"/projects/{pid}/live-heatmaps/{scan_id}", entry)

    def queue_job(self, pid: str, type: str, input: dict | None = None) -> dict:
        return self._json("POST", f"/projects/{pid}/jobs", {"type": type, "input": input or {}})["job"]

    # ---------- the live model ----------
    def model(self, pid: str) -> dict:
        """The whole model: {seq, levels, types, elements} (pages followed)."""
        out: dict | None = None
        cursor = None
        while True:
            q = {"cursor": cursor} if cursor else {}
            page = self._json("GET", f"/projects/{pid}/model", params=q)
            if out is None:
                out = page
            else:
                out["elements"].extend(page["elements"])
            cursor = page.get("next_cursor")
            if not cursor:
                out.pop("next_cursor", None)
                return out

    def model_seq(self, pid: str) -> dict:
        return self._json("GET", f"/projects/{pid}/model/seq")

    def model_ops(self, pid: str, ops: list[dict], *, note: str | None = None, author: dict | None = None) -> dict:
        """Apply ops as `author` (default the processing agent). A stale if_version raises ApiError(409)."""
        return self._json("POST", f"/projects/{pid}/model/ops", {"batch_id": str(uuid.uuid4()), "ops": ops, "note": note,
                                                                   **({"author": author} if author else {})})

    def model_base(self, pid: str, *, seq: int, glb: str, view: str | None, graph: str, index: str = "") -> dict:
        """Keys relative to projects/<pid>/ (as the viewer's assetBase resolves them)."""
        return self._json("POST", f"/projects/{pid}/model/base", {"seq": seq, "glb": glb, "view": view, "graph": graph, "index": index})

    # ---------- R2 (bucket 'uploads' is private project files; 'media' is public site files) ----------
    def download(self, key: str, dest: Path, *, bucket: str = "uploads", streams: int = 8) -> Path:
        """Big objects come down as parallel ranged reads (one stream through the Worker runs ~7 MB/s)."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        size = None
        try:
            size = int(self._req("HEAD", "/r2", params={"key": key, "bucket": bucket}, retries=1).headers.get("Content-Length") or 0) or None
        except ApiError:
            pass
        if not size or size < 2 * PART_DL:
            with self._req("GET", "/r2", params={"key": key, "bucket": bucket}, stream=True, timeout=3600) as r, open(dest, "wb") as f:
                for chunk in r.iter_content(8 * 1024 * 1024):
                    f.write(chunk)
            return dest
        from concurrent.futures import ThreadPoolExecutor

        with open(dest, "wb") as f:
            f.truncate(size)

        def piece(start: int) -> None:
            end = min(size, start + PART_DL) - 1
            with self._req("GET", "/r2", params={"key": key, "bucket": bucket}, stream=True, timeout=3600,
                           headers={"Range": f"bytes={start}-{end}"}) as r, open(dest, "r+b") as f:
                if r.status_code != 206:
                    raise ApiError(r.status_code, "expected a ranged read")
                f.seek(start)
                for chunk in r.iter_content(4 * 1024 * 1024):
                    f.write(chunk)

        with ThreadPoolExecutor(streams) as ex:
            for r in [ex.submit(piece, s) for s in range(0, size, PART_DL)]:
                r.result()
        return dest

    def exists(self, key: str, *, bucket: str = "uploads") -> bool:
        try:
            self._req("HEAD", "/r2", params={"key": key, "bucket": bucket}, retries=1)
            return True
        except ApiError as e:
            if e.status == 404:
                return False
            raise

    def list(self, prefix: str, *, bucket: str = "uploads") -> list[dict]:
        out, cursor = [], None
        while True:
            page = self._json("GET", "/r2/list", params={"prefix": prefix, "bucket": bucket, **({"cursor": cursor} if cursor else {})})
            out += page["objects"]
            cursor = page.get("cursor")
            if not cursor:
                return out

    def upload(self, path: Path, key: str, *, content_type: str = "application/octet-stream", bucket: str = "uploads") -> str:
        size = path.stat().st_size
        if size <= SINGLE_MAX:
            with open(path, "rb") as f:
                self._req("PUT", "/r2", params={"key": key, "bucket": bucket}, data=f,
                          headers={"Content-Type": content_type, "Content-Length": str(size)})
            return key
        up = self._json("POST", "/r2/create", {"key": key, "type": content_type, "bucket": bucket})
        from concurrent.futures import ThreadPoolExecutor

        def part(n: int) -> dict:
            with open(path, "rb") as f:
                f.seek((n - 1) * PART)
                chunk = f.read(PART)
            return self._json("PUT", "/r2/part", data=chunk, params={"key": key, "uploadId": up["uploadId"], "n": n, "bucket": bucket},
                              headers={"Content-Length": str(len(chunk))})

        with ThreadPoolExecutor(4) as ex:  # 4 × 64 MB in flight
            parts = list(ex.map(part, range(1, -(-size // PART) + 1)))
        self._json("POST", "/r2/complete", {"key": key, "uploadId": up["uploadId"], "parts": parts, "bucket": bucket})
        return key

    def upload_bytes(self, data: bytes, key: str, *, content_type: str = "application/octet-stream", bucket: str = "uploads") -> str:
        self._req("PUT", "/r2", params={"key": key, "bucket": bucket}, data=data,
                  headers={"Content-Type": content_type, "Content-Length": str(len(data))})
        return key

    def upload_json(self, obj: Any, key: str) -> str:
        return self.upload_bytes(json.dumps(obj, separators=(",", ":")).encode(), key, content_type="application/json")
