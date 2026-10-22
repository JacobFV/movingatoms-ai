"""A stand-in for ma_proc.api.Api for the ingest tests: R2 is a local directory, everything else is recorded."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path


class FakeApi:
    def __init__(self, root: Path, sources: dict[str, Path] | None = None):
        self.root = root
        self.sources = sources or {}
        self.calls: list[tuple] = []
        self.scans: dict[str, dict] = {}
        self.jobs: dict[str, dict] = {}
        self.files: list[dict] = []

    def _key(self, key: str) -> Path:
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def download(self, key, dest, *, bucket="uploads"):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.sources.get(key) or self._key(key), dest)
        return dest

    def upload(self, path, key, *, content_type="application/octet-stream", bucket="uploads"):
        shutil.copy(path, self._key(key))
        return key

    def upload_bytes(self, data, key, *, content_type="application/octet-stream", bucket="uploads"):
        self._key(key).write_bytes(data)
        return key

    def scan(self, scan_id, **fields):
        self.calls.append(("scan", scan_id, fields))
        self.scans.setdefault(scan_id, {}).update(fields)
        return self.scans[scan_id]

    def job(self, job_id, **fields):
        self.calls.append(("job", job_id, fields))
        self.jobs.setdefault(job_id, {}).update(fields)

    def add_file(self, pid, r2_key, **kw):
        f = {"id": str(uuid.uuid4()), "project_id": pid, "r2_key": r2_key, **kw}
        self.files.append(f)
        return f

    def update_file(self, file_id, **fields):
        self.calls.append(("file", file_id, fields))
        return {}

    def release(self, job_id):
        self.calls.append(("release", job_id, {}))
