"""Viewer layers (§11): LAS 1.4 files (point format 7: colour, intensity, classification = ma-v1 label) converted to
Potree 2.0 octrees by PotreeConverter, then uploaded to R2. The viewer colours labels by the `classification`
attribute and colours by `rgb` (which Potree reads as `rgba`)."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import laspy
import numpy as np

log = logging.getLogger(__name__)

FILES = ("metadata.json", "hierarchy.bin", "octree.bin")


def converter() -> str:
    for c in (os.environ.get("POTREE_CONVERTER"), shutil.which("PotreeConverter"), "/usr/local/bin/PotreeConverter"):
        if c and Path(c).exists():
            return c
    raise RuntimeError("PotreeConverter isn't installed (set POTREE_CONVERTER to its path).")


def las_header(bmin: np.ndarray) -> laspy.LasHeader:
    h = laspy.LasHeader(point_format=7, version="1.4")
    h.scales = np.array([0.001, 0.001, 0.001])
    h.offsets = np.floor(bmin)
    return h


def write_las(path: Path, parts, bmin: np.ndarray) -> int:
    """`parts` yields (xyz working frame, rgb uint16 (N,3) or None, intensity uint16 or None, labels uint8)."""
    h = las_header(bmin)
    n = 0
    with laspy.open(path, mode="w", header=h) as w:
        for xyz, rgb, inten, lab in parts:
            if not len(xyz):
                continue
            p = laspy.ScaleAwarePointRecord.zeros(len(xyz), header=h)
            p.x, p.y, p.z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
            if rgb is not None:
                p.red, p.green, p.blue = rgb[:, 0], rgb[:, 1], rgb[:, 2]
            if inten is not None:
                p.intensity = inten
            p.classification = lab
            w.write_points(p)
            n += len(xyz)
    return n


def convert(las: Path, out: Path, *, rgb: bool, intensity: bool, progress: Callable[[float], None] | None = None) -> Path:
    if out.exists():
        shutil.rmtree(out)
    attrs = ["classification"] + (["rgb"] if rgb else []) + (["intensity"] if intensity else [])
    # PotreeConverter's default encoding (metadata "encoding": "DEFAULT", uncompressed; never BROTLI): the heatmap's
    # attribute pages index points by byte offset, and the model jobs' Potree reader decodes only this encoding.
    # (Passing --encoding UNCOMPRESSED writes the same bytes but labels them "UNCOMPRESSED".)
    cmd = [converter(), str(las), "-o", str(out), "--attributes", *attrs]
    log.info("potree: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail: list[str] = []
    assert proc.stdout
    for line in proc.stdout:
        tail = (tail + [line.rstrip()])[-30:]
        if progress and "%" in line:  # "[40%, 3s], [...]"
            try:
                progress(float(line.split("%")[0].split("[")[-1]) / 100.0)
            except ValueError:
                pass
    if proc.wait() != 0 or not all((out / f).exists() for f in FILES):
        raise RuntimeError("PotreeConverter failed: " + " | ".join(tail[-6:]))
    return out


def upload(api, out: Path, prefix: str) -> None:
    """The three files of a Potree 2.0 octree, under `prefix` (an R2 key like projects/<pid>/scans/<sid>/potree)."""
    from concurrent.futures import ThreadPoolExecutor

    types = {"metadata.json": "application/json"}
    with ThreadPoolExecutor(len(FILES)) as ex:
        for r in [ex.submit(api.upload, out / f, f"{prefix}/{f}", content_type=types.get(f, "application/octet-stream")) for f in FILES]:
            r.result()
