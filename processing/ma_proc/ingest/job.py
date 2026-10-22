"""The ingest job (§9): a scan file in R2 becomes a labelled, viewable scan.

  inspecting → decoding → labelling → converting (the overview layer goes up first, so the scan opens early;
  then the full layer) → overview (pictures) → ready

Each stage reports to the scan (status, progress 0..1, stage_detail) and the job, so the app's processing screen
and project card move. `ready` makes the project active, prices the estimate and starts the agent (server side).
"""
from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import numpy as np

from ..api import Api
from . import classify, measure, potree, readers, render
from .store import PointStore

log = logging.getLogger(__name__)

OVERVIEW_POINTS = 250_000  # the preview layer: small, so the scan opens in seconds


class Reporter:
    """Progress to the scan and the job, at most every couple of seconds (and always on a stage change)."""

    def __init__(self, api: Api, job_id: str, scan_id: str):
        self.api, self.job_id, self.scan_id = api, job_id, scan_id
        self.status = None
        self.last = 0.0

    def __call__(self, status: str, progress: float, detail: str | None = None, *, force: bool = False, **fields) -> None:
        now = time.time()
        if not force and not fields and status == self.status and now - self.last < 2.0:
            return
        self.status, self.last = status, now
        p = float(min(0.99, max(0.0, progress)))
        self.api.scan(self.scan_id, status=status, progress=p, stage_detail=detail, **fields)
        self.api.job(self.job_id, status="running", stage=status, progress=p)


def run(api: Api, job: dict, claim: dict, *, work: Path, local_source: Path | None = None) -> dict:
    inp = job.get("input") or {}
    pid = job["project_id"]
    scan_id = inp["scan_id"]
    key = inp.get("r2_key")
    rep = Reporter(api, job["id"], scan_id)
    t0 = time.time()
    timings: dict[str, float] = {}

    # ---------- inspecting: fetch the file
    rep("inspecting", 0.0, "Fetching the scan", force=True)
    name = Path(key).name if key else "scan"
    src = local_source or api.download(key, work / "src" / name)
    files = [src]
    if readers.kind(src) == "zip":
        rep("inspecting", 0.5, "Opening the zip")
        files = readers.unzip_points(src, work / "unzipped")
    for f in files:
        readers.kind(f)  # unsupported formats fail here, in plain words
        if readers.kind(f) == "recap":
            raise readers.Unreadable("ReCap projects can't be read directly. Export the scan as E57 from ReCap and upload that.")
    positions = sum(readers.positions(f) for f in files)
    expected = sum(_expected_points(f) for f in files) or None
    timings["fetch"] = time.time() - t0

    # ---------- decoding: every point onto disk
    t = time.time()
    store = PointStore(work / "points")
    rep("decoding", 0.0, f"Decoding scan position 1 of {positions}", force=True)
    for f in files:
        for chunk in readers.read(f):
            store.append(chunk)
            frac = store.n / expected if expected else 0.5
            pos = min(positions, 1 + int(frac * positions))
            rep("decoding", frac, f"Decoding scan position {pos} of {positions}" if positions > 1 else f"Decoding {store.n:,} points")
    store.close()
    if store.n == 0:
        raise readers.Unreadable("This file has no points in it.")
    timings["decode"] = time.time() - t

    # ---------- measuring (part of decoding for the app): frame, bounds, levels, footprint
    t = time.time()
    rep("decoding", 0.97, "Measuring the scan")
    m = measure.measure(store)
    crs = readers.crs(files[0])
    brief = {
        "source": {"name": name, "format": src.suffix.lstrip(".").upper(), "bytes": int(src.stat().st_size), "scan_positions": positions},
        "points": int(store.n),
        "has_rgb": bool(store.has_rgb),
        "has_intensity": bool(store.has_intensity),
        "frame": m.frame.to_json(crs),
        "bounds": m.bounds,
        "extent_m": m.extent,
        "footprint_m2": m.footprint_m2,
        "levels_guess": m.levels,
        "density": {"median_spacing_mm": m.spacing_mm},
        "warnings": m.warnings,
    }
    rep("labelling", 0.0, "Labelling walls, floors and ceilings", force=True,
        point_count=int(store.n), bounds=m.bounds, frame=brief["frame"], brief=brief)
    timings["measure"] = time.time() - t

    # ---------- labelling: classify the even sample, then every point by its nearest sampled neighbour
    t = time.time()
    lab_s = classify.classify(m.feats, m.levels, lambda f, text: rep("labelling", 0.7 * f, text))
    xyz_all = store.xyz
    for s, e in store.chunks(2_000_000):
        w = m.frame.apply(np.asarray(xyz_all[s:e]))
        _, nn = m.feats.tree.query(w, k=1, workers=-1)
        store.labels[s:e] = lab_s[nn]
        rep("labelling", 0.7 + 0.3 * e / store.n, "Labelling every point")
    store.labels.flush()
    counts = classify.counts(np.asarray(store.labels))
    labels = {"scheme": "ma-v1", "method": classify.METHOD, "counts": counts, "names": classify.names()}
    brief["labels"] = labels
    timings["label"] = time.time() - t

    # ---------- converting: the overview layer first (opens the scan), then the full layer
    t = time.time()
    scan_prefix = f"projects/{pid}/scans/{scan_id}"
    rep("converting", 0.0, "Building the overview layer", force=True)
    ov_idx = m.sample_idx if len(m.sample_idx) <= OVERVIEW_POINTS else np.sort(np.random.default_rng(5).choice(m.sample_idx, OVERVIEW_POINTS, replace=False))
    bmin = np.array(m.bounds["min"])
    ov_las = work / "overview.las"
    n_ov = potree.write_las(ov_las, _parts(store, m.frame, ov_idx), bmin)
    ov_dir = potree.convert(ov_las, work / "potree-overview", rgb=store.has_rgb, intensity=store.has_intensity,
                            progress=lambda f: rep("converting", 0.1 * f, "Building the overview layer"))
    potree.upload(api, ov_dir, f"{scan_prefix}/potree-overview")
    viewer = {"overview": {"potree_prefix": f"{scan_prefix}/potree-overview", "points": int(n_ov), "has_labels": True}}
    rep("converting", 0.15, "Building the full-detail layer", force=True, viewer=viewer, labels=labels, brief=brief)
    full_prefix = f"{scan_prefix}/potree"
    if len(ov_idx) == store.n:
        # a small scan: the overview layer is every point; the same files serve as the full layer
        full_las, full_dir, n_full = ov_las, ov_dir, n_ov
    else:
        full_las = work / "full.las"
        n_full = potree.write_las(full_las, _parts(store, m.frame, None, lambda f: rep("converting", 0.15 + 0.2 * f, "Building the full-detail layer")), bmin)
        full_dir = potree.convert(full_las, work / "potree", rgb=store.has_rgb, intensity=store.has_intensity,
                                  progress=lambda f: rep("converting", 0.35 + 0.45 * f, "Building the full-detail layer"))
    rep("converting", 0.85, "Uploading the full-detail layer")
    potree.upload(api, full_dir, full_prefix)
    viewer["full"] = {"potree_prefix": full_prefix, "points": int(n_full), "has_labels": True}
    timings["convert"] = time.time() - t

    # ---------- overview pictures
    t = time.time()
    rep("overview", 0.0, "Rendering overview images", force=True, viewer=viewer)
    overview = _pictures(api, pid, scan_prefix, store, m, ov_idx, lab_s if len(ov_idx) == len(m.sample_idx) else None)
    brief["overview"] = [v["key"] for v in overview.values()]
    timings["overview"] = time.time() - t

    # ---------- ready
    timings["total"] = time.time() - t0
    api.scan(scan_id, status="ready", progress=1, stage_detail=None, potree_prefix=full_prefix, viewer=viewer,
             labels=labels, overview=overview, brief=brief, point_count=int(store.n), bounds=m.bounds, frame=brief["frame"])
    # every point with its label, for the model jobs (fit to scan reads it): after `ready`, so nobody waits on it
    t = time.time()
    laz = work / "labelled.laz"
    _to_laz(full_las, laz)
    api.upload(laz, f"{scan_prefix}/labelled.laz", content_type="application/vnd.laszip")
    timings["labelled"] = time.time() - t
    log.info("ingest %s: %s points in %.1fs %s", scan_id, f"{store.n:,}", timings["total"], {k: round(v, 1) for k, v in timings.items()})
    return {"scan_id": scan_id, "points": int(store.n), "labels": counts, "timings": {k: round(v, 1) for k, v in timings.items()}}


def _to_laz(las: Path, laz: Path) -> None:
    """LAS → LAZ (lazrs), in chunks: about a fifth of the bytes to store and fetch."""
    import laspy

    with laspy.open(las) as r, laspy.open(laz, mode="w", header=r.header, do_compress=True) as w:
        for pts in r.chunk_iterator(2_000_000):
            w.write_points(pts)


def _expected_points(path: Path) -> int:
    try:
        k = readers.kind(path)
        if k in ("las", "laz"):
            import laspy

            with laspy.open(path) as f:
                return int(f.header.point_count)
        if k == "e57":
            import pye57

            e = pye57.E57(str(path))
            return sum(int(e.get_header(i).point_count) for i in range(e.scan_count))
        if k == "ply":
            from plyfile import PlyData

            return int(PlyData.read(str(path), mmap=True)["vertex"].count)
    except Exception:
        pass
    return 0


def _parts(store: PointStore, frame: measure.Frame, idx: np.ndarray | None, progress=None):
    """(xyz, rgb, intensity, labels) chunks for a LAS file: the given points, or all of them."""
    rgb_on, int_on = store.has_rgb, store.has_intensity
    if idx is not None:
        for s in range(0, len(idx), 2_000_000):
            sel = idx[s : s + 2_000_000]
            yield (frame.apply(np.asarray(store.xyz[sel])), np.asarray(store.rgb[sel]) if rgb_on else None,
                   np.asarray(store.intensity[sel]) if int_on else None, np.asarray(store.labels[sel]))
        return
    for s, e in store.chunks(3_000_000):
        yield (frame.apply(np.asarray(store.xyz[s:e])), np.asarray(store.rgb[s:e]) if rgb_on else None,
               np.asarray(store.intensity[s:e]) if int_on else None, np.asarray(store.labels[s:e]))
        if progress:
            progress(e / store.n)


def _pictures(api: Api, pid: str, prefix: str, store: PointStore, m: measure.Measured, idx: np.ndarray, lab: np.ndarray | None) -> dict:
    xyz = m.frame.apply(np.asarray(store.xyz[idx]))
    if lab is None:
        lab = np.asarray(store.labels[idx])
    if store.has_rgb:
        col = (np.asarray(store.rgb[idx]) >> 8).astype(np.uint8)
        # outside points and noise read as clutter in a picture of the building
        keep = (lab != classify.NOISE) & (lab != classify.OUTSIDE)
    else:
        col = render.label_colors(lab)
        keep = lab != classify.NOISE
    xyz, col = xyz[keep], col[keep]
    ceilings = [l["z"] for l in m.levels if l["kind"] == "ceiling"]
    cut = (min(ceilings) - 0.15) if ceilings else None  # a top view looks into the rooms, under the ceiling
    lab_col = render.label_colors(lab[keep])
    views = [
        ("top", col, {"cut_ceiling": cut}, store.has_rgb),
        ("top_labels", lab_col, {"cut_ceiling": cut}, False),
        ("iso_ne", col, {}, store.has_rgb),
        ("iso_sw", col, {}, store.has_rgb),
        ("side_x", col, {}, store.has_rgb),
        ("side_y", col, {}, store.has_rgb),
    ]

    def one(v):
        view, c, kw, stretch = v
        img = render.render(xyz, c, "top" if view == "top_labels" else view, stretch=stretch, **kw)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        key = f"{prefix}/overview-{view}.png"
        api.upload_bytes(buf.getvalue(), key, content_type="image/png")
        f = api.add_file(pid, key, kind="image", name=f"overview-{view}.png", content_type="image/png", meta={"scan_prefix": prefix, "view": view})
        return view, {"key": key, "file_id": f["id"]}

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(3) as ex:
        return dict(ex.map(one, views))
