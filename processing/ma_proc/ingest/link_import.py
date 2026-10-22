"""A scan from a link (§4 imports): stream it to disk, store it in R2 as the project's source file, then ingest it in
the same job (no second download)."""
from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from ..api import Api, ApiError
from . import job as ingest

log = logging.getLogger(__name__)

MAX_BYTES = 200 * 1024**3


def _direct(url: str) -> str:
    """Share links that need a nudge to give the file itself."""
    u = urlparse(url)
    if "dropbox.com" in u.netloc:
        return re.sub(r"([?&])dl=0", r"\1dl=1", url) if "dl=0" in url else url + ("&" if u.query else "?") + "dl=1"
    m = re.match(r"https://drive\.google\.com/file/d/([^/]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}&confirm=t"
    return url


def run(api: Api, job: dict, claim: dict, *, work: Path) -> dict:
    inp = job.get("input") or {}
    scan_id, key, url = inp["scan_id"], inp["r2_key"], inp["url"]
    name = Path(key).name or unquote(Path(urlparse(url).path).name) or "imported-scan"
    dest = work / "src" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    api.scan(scan_id, status="importing", progress=0, stage_detail="Copying from the link")
    t = 0.0
    with requests.get(_direct(url), stream=True, timeout=60, allow_redirects=True, headers={"User-Agent": "MovingAtoms-Importer/1.0"}) as r:
        if r.status_code >= 400:
            raise ingest.readers.Unreadable(f"The link answered {r.status_code}. Check that it's public and points at the file itself.")
        ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
        if "text/html" in ctype:
            raise ingest.readers.Unreadable("The link opens a web page, not the scan file. Share a direct download link.")
        total = int(r.headers.get("Content-Length") or 0)
        limit = int(os.environ.get("MA_MAX_SOURCE_BYTES") or 0)
        if limit and total > limit:
            raise ingest.readers.TooBig(f"{total} bytes is over this worker's {limit}")
        got = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8 * 1024 * 1024):
                f.write(chunk)
                got += len(chunk)
                if got > MAX_BYTES:
                    raise ingest.readers.Unreadable("Files can be up to 200 GB.")
                if time.time() - t > 2:
                    t = time.time()
                    frac = got / total if total else 0.0
                    api.scan(scan_id, status="importing", progress=min(0.99, frac),
                             stage_detail=f"Copying from the link ({got / 1e9:.2f} GB{' of ' + format(total / 1e9, '.2f') + ' GB' if total else ''})")
                    api.job(job["id"], status="running", stage="importing", progress=min(0.99, frac))
    api.scan(scan_id, status="importing", progress=0.99, stage_detail="Storing the scan")
    api.upload(dest, key)
    try:
        api.update_file(inp["file_id"], status="ready", size_bytes=dest.stat().st_size, content_type=ctype or None)
    except ApiError as e:  # an older server without the endpoint: the scan still goes on
        log.warning("file %s not marked ready: %s", inp.get("file_id"), e)
    result = ingest.run(api, job, claim, work=work, local_source=dest)
    return {"imported_bytes": dest.stat().st_size, **result}
