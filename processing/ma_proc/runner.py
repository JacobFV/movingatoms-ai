"""The processing worker: claim jobs from the site and run them.

    WORKER_TOKEN=… python -m ma_proc.runner            # loop forever
    WORKER_TOKEN=… python -m ma_proc.runner --once     # one job (or none), then exit

Each job runs in its own work directory (removed afterwards). A heartbeat keeps the claim alive while a long stage
runs (claims lapse after 15 minutes without an update). A failed ingest marks its scan unreadable in plain words.

MA_MAX_SOURCE_BYTES (e.g. on a Cloudflare Containers instance: ~20 GB disk, 12 GiB RAM) makes this worker hand back
scans bigger than that, so a bigger machine takes them. On SIGTERM the job in hand is released, not failed.
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from typing import Callable

from .api import Api, ApiError

log = logging.getLogger("ma_proc")

TYPES = ["ingest", "link_import", "model_fit", "build", "heatmap"]
# handlers that live in other modules: imported when a job of that type arrives
LAZY = {"model_fit": "ma_proc.model.fit", "build": "ma_proc.model.build", "heatmap": "ma_proc.model.heatmap"}


class Shutdown(BaseException):
    """SIGTERM arrived mid-job: stop, release the job, exit."""


MAX_SOURCE = int(os.environ.get("MA_MAX_SOURCE_BYTES") or 0)
current: dict = {}


def too_big(job: dict) -> bool:
    size = int((job.get("input") or {}).get("size") or 0)
    return bool(MAX_SOURCE and job["type"] == "ingest" and size > MAX_SOURCE)


class JsonFormatter(logging.Formatter):
    def format(self, r: logging.LogRecord) -> str:
        out = {"t": round(r.created, 3), "level": r.levelname, "logger": r.name, "msg": r.getMessage()}
        for k in ("job", "type", "project"):
            if hasattr(r, k):
                out[k] = getattr(r, k)
        if r.exc_info:
            out["exc"] = self.formatException(r.exc_info)
        return json.dumps(out)


def handler(kind: str) -> Callable:
    if kind == "ingest":
        from .ingest import job

        return job.run
    if kind == "link_import":
        from .ingest import link_import

        return link_import.run
    if kind in LAZY:
        try:
            return importlib.import_module(LAZY[kind]).run
        except ImportError as e:
            raise RuntimeError(f"This worker can't run {kind} jobs yet ({e}).") from e
    raise RuntimeError(f"Unknown job type: {kind}")


class Heartbeat:
    """Touch the job every `every` seconds so the claim doesn't lapse during a long stage."""

    def __init__(self, api: Api, job_id: str, every: float = 45.0):
        self.api, self.job_id, self.every = api, job_id, every
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(self.every):
            try:
                self.api.job(self.job_id, status="running")
            except Exception as e:  # never kill the job over a missed heartbeat
                log.warning("heartbeat failed: %s", e)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()


def plain(e: BaseException) -> str:
    """The message a customer sees for a failure."""
    from .ingest.readers import Unreadable

    if isinstance(e, Unreadable):
        return str(e)
    if isinstance(e, MemoryError):
        return "This scan is too large for one processing machine. Our team has been told."
    return "We couldn't process this scan. Our team has been told and will look at it."


def run_one(api: Api, claim: dict, workroot: Path) -> str:
    """Run a claimed job: "done", "failed" or "released"."""
    job = claim["job"]
    kind = job["type"]
    extra = {"job": job["id"], "type": kind, "project": job["project_id"]}
    if too_big(job):
        log.info("too big for this worker (%s bytes): released", (job.get("input") or {}).get("size"), extra=extra)
        api.release(job["id"])
        return "released"
    work = Path(tempfile.mkdtemp(prefix=f"{kind}-{job['id'][:8]}-", dir=workroot))
    t0 = time.time()
    log.info("start", extra=extra)
    current["job"] = job["id"]
    try:
        with Heartbeat(api, job["id"]):
            api.job(job["id"], status="running", stage="starting", progress=0)
            fn = handler(kind)
            kw = {"work": work} if kind in ("ingest", "link_import") else {}
            result = fn(api, job, claim, **kw) or {}
        api.job(job["id"], status="done", stage=None, progress=1, result=result)
        log.info("done in %.1fs", time.time() - t0, extra=extra)
        return "done"
    except Shutdown:
        log.warning("shutting down mid-job: released", extra=extra)
        api.release(job["id"])
        raise
    except Exception as e:
        from .ingest.readers import TooBig

        if isinstance(e, TooBig):
            log.info("too big for this worker (%s): released", e, extra=extra)
            api.release(job["id"])
            return "released"
        log.error("failed: %s", e, exc_info=True, extra=extra)
        detail = f"{type(e).__name__}: {e}"[:2000]
        try:
            api.job(job["id"], status="error", error=detail, result={"trace": traceback.format_exc()[-4000:]})
            if kind in ("ingest", "link_import") and (job.get("input") or {}).get("scan_id"):
                api.scan(job["input"]["scan_id"], status="error", error=plain(e), stage_detail=None)
        except ApiError as e2:
            log.error("couldn't report the failure: %s", e2, extra=extra)
        return "failed"
    finally:
        current.pop("job", None)
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Moving Atoms processing worker")
    ap.add_argument("--once", action="store_true", help="run at most one job, then exit")
    ap.add_argument("--types", default=",".join(TYPES), help="job types to claim (comma separated)")
    ap.add_argument("--poll", type=float, default=1.5, help="seconds between polls when idle")
    ap.add_argument("--work", default=os.environ.get("MA_WORK_DIR") or os.environ.get("MA_WORK") or tempfile.gettempdir(), help="work directory root (MA_WORK_DIR)")
    ap.add_argument("--log", default=os.environ.get("MA_LOG", "json"), choices=["json", "text"])
    args = ap.parse_args(argv)

    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(JsonFormatter() if args.log == "json" else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=os.environ.get("MA_LOG_LEVEL", "INFO"), handlers=[h])

    api = Api.from_env()
    workroot = Path(args.work)
    workroot.mkdir(parents=True, exist_ok=True)
    types = [t for t in args.types.split(",") if t]
    stopping = threading.Event()

    def on_term(*_):
        stopping.set()
        if current.get("job"):
            raise Shutdown()  # interrupts the job; run_one releases it

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    backoff = 0.0
    log.info("worker up: %s, types %s", api.base, types)
    while not stopping.is_set():
        try:
            claim = api.claim(types, max_size=MAX_SOURCE or None)
        except Exception as e:
            log.warning("claim failed: %s", e)
            claim = None
            if args.once:
                return 1
        if claim:
            try:
                outcome = run_one(api, claim, workroot)
            except Shutdown:
                return 0
            if args.once:
                return 0 if outcome != "failed" else 1
            if outcome == "released":
                # the same job would come straight back: give a bigger machine time to take it
                backoff = min(300.0, max(30.0, backoff * 2))
                stopping.wait(backoff)
            else:
                backoff = 0.0
            continue
        if args.once:
            log.info("no jobs")
            return 0
        stopping.wait(args.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
