"""The `model_fit` job (§17.5, POST …/model/fit): fit elements to the scan points around them.

Walls: both faces as planes along the wall's normal → position and thickness. Columns: rectangular sections from the
points' extent in the column's own axes, round ones by a circle fit. Pipes and round ducts: a circle fit across the
axis → axis shift and diameter. Rectangular ducts and beams: the section's extent across the axis. Slabs: the top face's
height. Doors, windows, openings and levels follow their hosts and are skipped, as are meshes.

The changes are applied as the person who asked (so they can undo them), with if_version; the result is what
web/src/viewer/edit/fit.ts reads: {fitted: [{id, changed, p95_mm, note?}], skipped: [{id, reason}], seq}.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from .geometry import Model, _num, column_section, duct_section, is_parametric, section_axes, slab_rings, wall_frame
from .points import load_points, ready_scans

MIN_POINTS = 40
BAND = 0.15  # how far from the modelled surface scan points still count, m
MOVE_MM = 2.0  # changes smaller than this are noise: the element is left as it is
SKIP = {"door": "doors follow their wall", "window": "windows follow their wall", "opening": "openings follow their wall", "level": "levels follow their elements"}


def _robust(values: np.ndarray, iters: int = 3) -> tuple[float, np.ndarray]:
    """Median with 3·MAD outlier rejection; returns (centre, inlier mask)."""
    mask = np.ones(len(values), dtype=bool)
    c = float(np.median(values))
    for _ in range(iters):
        r = np.abs(values - c)
        mad = float(np.median(r[mask])) * 1.4826 + 1e-4
        mask = r <= 3 * mad
        if mask.sum() < 3:
            break
        c = float(np.median(values[mask]))
    return c, mask


def _stats(residuals_m: np.ndarray, coverage: float) -> dict:
    r = np.abs(residuals_m) * 1000
    return {"p50_mm": round(float(np.percentile(r, 50)), 1), "p95_mm": round(float(np.percentile(r, 95)), 1), "coverage_pct": round(coverage * 100, 1)}


def _circle_fit(xy: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """Kåsa algebraic circle fit, then 2 rounds of rejecting points beyond 3σ. Returns (centre, radius, residuals)."""
    mask = np.ones(len(xy), dtype=bool)
    c, r = xy.mean(axis=0), 0.0
    for _ in range(3):
        p = xy[mask]
        A = np.column_stack([2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))])
        b = (p ** 2).sum(axis=1)
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        c = sol[:2]
        r = math.sqrt(max(sol[2] + c @ c, 0.0))
        res = np.linalg.norm(xy - c, axis=1) - r
        s = float(np.std(res[mask])) + 1e-4
        mask = np.abs(res) <= 3 * s
        if mask.sum() < 8:
            break
    return c, r, (np.linalg.norm(xy - c, axis=1) - r)[mask]


def _grid_coverage(a: np.ndarray, b: np.ndarray, a_range: tuple[float, float], b_range: tuple[float, float], cell: float = 0.25) -> float:
    na = max(1, int(math.ceil((a_range[1] - a_range[0]) / cell)))
    nb = max(1, int(math.ceil((b_range[1] - b_range[0]) / cell)))
    ia = np.clip(((a - a_range[0]) / cell).astype(int), 0, na - 1)
    ib = np.clip(((b - b_range[0]) / cell).astype(int), 0, nb - 1)
    return len(set(zip(ia.tolist(), ib.tolist()))) / (na * nb)


def fit_wall(e: dict, m: Model, tree: cKDTree, pts: np.ndarray) -> tuple[dict | None, dict]:
    f = wall_frame(e, m)
    if not f:
        return None, {"note": "the wall has no start and end"}
    mid = f.start + f.u * f.length / 2
    zc = (f.base + f.top) / 2
    radius = math.hypot(f.length / 2 + 0.1, (f.top - f.base) / 2, f.half + BAND)
    idx = tree.query_ball_point([mid[0], mid[1], zc], radius)
    if len(idx) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    p = pts[idx]
    d = p[:, :2] - f.start
    along, across, z = d @ f.u, d @ f.v, p[:, 2]
    keep = (along > 0.05) & (along < f.length - 0.05) & (z > f.base + 0.1) & (z < f.top - 0.1) & (np.abs(across) < f.half + BAND)
    along, across, z = along[keep], across[keep], z[keep]
    if len(across) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    side_a, side_b = across > 0, across < 0
    faces = {}
    for name, sel in (("a", side_a), ("b", side_b)):
        if sel.sum() >= MIN_POINTS:
            c, mask = _robust(across[sel])
            faces[name] = (c, across[sel][mask] - c, along[sel][mask], z[sel][mask])
    if not faces:
        return None, {"note": "not enough scan points on either face"}
    thickness = 2 * f.half
    if "a" in faces and "b" in faces:
        fa, fb = faces["a"][0], faces["b"][0]
        new_t = fa - fb
        if new_t > 0.02:
            shift, thickness = (fa + fb) / 2, new_t
        else:
            shift = 0.0
    elif "a" in faces:
        shift = faces["a"][0] - f.half
    else:
        shift = faces["b"][0] + f.half
    res = np.concatenate([fc[1] for fc in faces.values()])
    cov_a = np.concatenate([fc[2] for fc in faces.values()])
    cov_z = np.concatenate([fc[3] for fc in faces.values()])
    coverage = _grid_coverage(cov_a, cov_z, (0, f.length), (f.base, f.top)) / max(1, len(faces)) * len(faces)
    fit = _stats(res, min(1.0, coverage))
    changed = abs(shift) * 1000 >= MOVE_MM or abs(thickness - 2 * f.half) * 1000 >= MOVE_MM
    if not changed:
        return None, {"fit": fit, "note": "already within 2 mm of the scan"}
    params = e.get("params") or {}
    s = np.array(params["start"][:2], dtype=float) + f.v * shift
    t = np.array(params["end"][:2], dtype=float) + f.v * shift
    patch = {"start": [round(float(s[0]), 4), round(float(s[1]), 4)], "end": [round(float(t[0]), 4), round(float(t[1]), 4)], "thickness": round(float(thickness), 4)}
    return patch, {"fit": fit}


def fit_column(e: dict, m: Model, tree: cKDTree, pts: np.ndarray) -> tuple[dict | None, dict]:
    p = e.get("params") or {}
    pos = p.get("position")
    rings = column_section(p)
    if not pos or not rings:
        return None, {"note": "the column has no position or section"}
    base, top = m.vertical_extent(e)
    s = p.get("section") or {}
    size = max(_num(s.get("w"), 0), _num(s.get("d"), 0), _num(s.get("d"), 0))
    idx = tree.query_ball_point([pos[0], pos[1], (base + top) / 2], math.hypot(size / 2 + BAND, (top - base) / 2))
    if len(idx) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    q = pts[idx]
    q = q[(q[:, 2] > base + 0.1) & (q[:, 2] < top - 0.1)]
    if len(q) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    rot = _num(p.get("rotation"), 0.0)
    w_ax, d_ax = np.array([math.cos(rot), math.sin(rot)]), np.array([-math.sin(rot), math.cos(rot)])
    rel = q[:, :2] - np.array(pos[:2], dtype=float)
    if s.get("shape") == "circle":
        c, r, res = _circle_fit(rel)
        if not (0.02 < r < size):
            return None, {"note": "no round column found in the scan here"}
        new_pos = np.array(pos[:2], dtype=float) + c
        patch = {"position": [round(float(new_pos[0]), 4), round(float(new_pos[1]), 4)], "section": {**s, "d": round(2 * r, 4)}}
        moved = max(np.linalg.norm(c), abs(2 * r - s["d"])) * 1000
        fit = _stats(res, 1.0)
    else:
        w, d = rel @ w_ax, rel @ d_ax
        sel = (np.abs(w) < s["w"] / 2 + BAND) & (np.abs(d) < s["d"] / 2 + BAND)
        w, d = w[sel], d[sel]
        if len(w) < MIN_POINTS:
            return None, {"note": "not enough scan points here"}
        w0, w1 = np.percentile(w, [1, 99])
        d0, d1 = np.percentile(d, [1, 99])
        cw, cd = (w0 + w1) / 2, (d0 + d1) / 2
        new_pos = np.array(pos[:2], dtype=float) + w_ax * cw + d_ax * cd
        nw, nd = w1 - w0, d1 - d0
        res = np.minimum(np.abs(np.abs(w - cw) - nw / 2), np.abs(np.abs(d - cd) - nd / 2))
        patch = {"position": [round(float(new_pos[0]), 4), round(float(new_pos[1]), 4)], "section": {**s, "w": round(float(nw), 4), "d": round(float(nd), 4)}}
        moved = max(math.hypot(cw, cd), abs(nw - s["w"]), abs(nd - s["d"])) * 1000
        fit = _stats(res, 1.0)
    if moved < MOVE_MM:
        return None, {"fit": fit, "note": "already within 2 mm of the scan"}
    return patch, {"fit": fit}


def _axis_points(start: np.ndarray, end: np.ndarray, reach: float, tree: cKDTree, pts: np.ndarray):
    axis = end - start
    length = float(np.linalg.norm(axis))
    u = axis / length
    idx = tree.query_ball_point((start + end) / 2, math.hypot(length / 2, reach))
    if not idx:
        return None
    q = pts[idx]
    t = (q - start) @ u
    keep = (t > 0.03 * length) & (t < 0.97 * length)
    q = q[keep]
    radial = (q - start) - np.outer((q - start) @ u, u)
    keep = np.linalg.norm(radial, axis=1) < reach
    return u, q[keep], radial[keep]


def fit_round(e: dict, od: float, key: str, tree: cKDTree, pts: np.ndarray, set_size) -> tuple[dict | None, dict]:
    p = e.get("params") or {}
    start, end = np.array(p["start"], dtype=float), np.array(p["end"], dtype=float)
    got = _axis_points(start, end, od / 2 + BAND, tree, pts)
    if not got or len(got[1]) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    u, q, radial = got
    b_ax, h_ax = section_axes(u)
    xy = np.column_stack([radial @ b_ax, radial @ h_ax])
    c, r, res = _circle_fit(xy)
    if not (0.005 < r < od):
        return None, {"note": "better fit not found"}
    shift = b_ax * c[0] + h_ax * c[1]
    fit = _stats(res, min(1.0, len(q) / 200))
    if max(np.linalg.norm(shift), abs(2 * r - od)) * 1000 < MOVE_MM:
        return None, {"fit": fit, "note": "already within 2 mm of the scan"}
    ns, ne = start + shift, end + shift
    patch = {"start": [round(float(x), 4) for x in ns], "end": [round(float(x), 4) for x in ne], **set_size(round(2 * r, 4))}
    return patch, {"fit": fit}


def fit_box_member(e: dict, w: float, h: float, roll: float, tree: cKDTree, pts: np.ndarray, set_size) -> tuple[dict | None, dict]:
    p = e.get("params") or {}
    start, end = np.array(p["start"], dtype=float), np.array(p["end"], dtype=float)
    got = _axis_points(start, end, math.hypot(w, h) / 2 + BAND, tree, pts)
    if not got or len(got[1]) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    u, q, radial = got
    b_ax, h_ax = section_axes(u, roll)
    bb, hh = radial @ b_ax, radial @ h_ax
    sel = (np.abs(bb) < w / 2 + BAND) & (np.abs(hh) < h / 2 + BAND)
    bb, hh = bb[sel], hh[sel]
    if len(bb) < MIN_POINTS:
        return None, {"note": "not enough scan points here"}
    b0, b1 = np.percentile(bb, [1, 99])
    h0, h1 = np.percentile(hh, [1, 99])
    cb, ch = (b0 + b1) / 2, (h0 + h1) / 2
    nw, nh = b1 - b0, h1 - h0
    res = np.minimum(np.abs(np.abs(bb - cb) - nw / 2), np.abs(np.abs(hh - ch) - nh / 2))
    fit = _stats(res, 1.0)
    if max(math.hypot(cb, ch), abs(nw - w), abs(nh - h)) * 1000 < MOVE_MM:
        return None, {"fit": fit, "note": "already within 2 mm of the scan"}
    shift = b_ax * cb + h_ax * ch
    patch = {"start": [round(float(x), 4) for x in start + shift], "end": [round(float(x), 4) for x in end + shift], **set_size(round(float(nw), 4), round(float(nh), 4))}
    return patch, {"fit": fit}


def _in_polygon(xy: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """Even-odd ray casting, vectorised over points."""
    x, y = xy[:, 0], xy[:, 1]
    inside = np.zeros(len(xy), dtype=bool)
    for (x0, y0), (x1, y1) in zip(ring, np.roll(ring, -1, axis=0)):
        crosses = (y0 > y) != (y1 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
        inside ^= crosses & (x < xc)
    return inside


def fit_slab(e: dict, m: Model, tree: cKDTree, pts: np.ndarray) -> tuple[dict | None, dict]:
    p = e.get("params") or {}
    rings = slab_rings(p)
    if not rings:
        return None, {"note": "the slab has no outline"}
    top = m.elevation(e.get("level_id")) + _num(p.get("offset"), 0.0)
    outer = rings[0]
    lo, hi = outer.min(axis=0), outer.max(axis=0)
    centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, top])
    idx = tree.query_ball_point(centre, math.hypot((hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2, BAND))
    q = pts[idx] if idx else np.zeros((0, 3))
    inside = _in_polygon(q[:, :2], outer) if len(q) else np.zeros(0, dtype=bool)
    q = q[inside & (np.abs(q[:, 2] - top) < BAND)]
    if len(q) < MIN_POINTS:
        return None, {"note": "not enough scan points on the slab"}
    z, mask = _robust(q[:, 2])
    fit = _stats(q[mask, 2] - z, _grid_coverage(q[:, 0], q[:, 1], (lo[0], hi[0]), (lo[1], hi[1]), 0.5))
    dz = z - top
    if abs(dz) * 1000 < MOVE_MM:
        return None, {"fit": fit, "note": "already within 2 mm of the scan"}
    return {"offset": round(_num(p.get("offset"), 0.0) + dz, 4)}, {"fit": fit}


def fit_element(e: dict, m: Model, tree: cKDTree, pts: np.ndarray) -> tuple[dict | None, dict]:
    kind = e.get("kind")
    p = e.get("params") or {}
    if kind == "wall":
        return fit_wall(e, m, tree, pts)
    if kind == "column":
        return fit_column(e, m, tree, pts)
    if kind == "slab":
        return fit_slab(e, m, tree, pts)
    if kind == "pipe" and _num(p.get("od"), 0) > 0 and p.get("start") and p.get("end"):
        return fit_round(e, float(p["od"]), "od", tree, pts, lambda d: {"od": d})
    if kind == "duct" and p.get("start") and p.get("end"):
        s = p.get("section") or {}
        if s.get("shape") == "round" and _num(s.get("d"), 0) > 0:
            return fit_round(e, float(s["d"]), "d", tree, pts, lambda d: {"section": {**s, "d": d}})
        if s.get("shape") == "rect" and duct_section(p):
            return fit_box_member(e, float(s["w"]), float(s["h"]), _num(p.get("roll"), 0.0), tree, pts, lambda w, h: {"section": {**s, "w": w, "h": h}})
    if kind == "beam" and p.get("start") and p.get("end"):
        prof = p.get("profile") or {}
        if prof.get("shape") == "rect" and _num(prof.get("w"), 0) > 0 and _num(prof.get("h"), 0) > 0:
            return fit_box_member(e, float(prof["w"]), float(prof["h"]), _num(p.get("roll"), 0.0), tree, pts, lambda w, h: {"profile": {**prof, "w": w, "h": h}})
        w, h = _num(prof.get("b", prof.get("w")), 0), _num(prof.get("h", prof.get("d")), 0)
        if w > 0 and h > 0:  # other profiles: move only
            return fit_box_member(e, w, h, _num(p.get("roll"), 0.0), tree, pts, lambda _w, _h: {})
    return None, {"note": "nothing to fit for this kind"}


def fit_model(read: dict, ids: list[str], pts: np.ndarray) -> tuple[list[dict], list[dict], list[dict]]:
    """(ops, fitted, skipped) for the given element ids against the points."""
    m = Model(read)
    tree = cKDTree(pts) if len(pts) else None
    ops, fitted, skipped = [], [], []
    for id in ids:
        e = m.get(id)
        if not e:
            skipped.append({"id": id, "reason": "not in the model"})
            continue
        if e.get("kind") in SKIP:
            skipped.append({"id": id, "reason": SKIP[e["kind"]]})
            continue
        if not is_parametric(e):
            skipped.append({"id": id, "reason": "meshes aren't fitted"})
            continue
        if tree is None:
            fitted.append({"id": id, "changed": False, "p95_mm": None, "note": "no scan points"})
            continue
        patch, info = fit_element(e, m, tree, pts)
        fit = info.get("fit")
        provenance = {**(e.get("provenance") or {}), "status": "observed", "method": "fit", **({"fit": fit} if fit else {})}
        if patch:
            ops.append({"op": "update", "id": id, "patch": {"params": patch, "provenance": provenance}, "if_version": int(e.get("version") or 1)})
            fitted.append({"id": id, "changed": True, "before": {k: (e.get("params") or {}).get(k) for k in patch}, "after": patch, "p95_mm": fit and fit["p95_mm"]})
        else:
            if fit:
                ops.append({"op": "update", "id": id, "patch": {"provenance": {"fit": fit}}, "if_version": int(e.get("version") or 1)})
            fitted.append({"id": id, "changed": False, "p95_mm": fit and fit["p95_mm"], "note": info.get("note")})
    return ops, fitted, skipped


def run(api: Any, job: dict, claim: dict) -> dict:
    pid = job["project_id"]
    inp = job.get("input") or {}
    ids = [str(x) for x in inp.get("element_ids") or []][:500]
    by = inp.get("by")
    author = {"kind": "agent", "id": "agent", "name": "Atom"} if by in (None, "agent") else {"kind": "user", "id": f"user:{by}", "name": "Fit to scan"}
    scans = ready_scans(claim.get("scans") or [])
    if not scans:
        raise ValueError("no ready scan to fit to")
    api.job(job["id"], stage="loading the scan", progress=0.1)
    with tempfile.TemporaryDirectory() as d:
        clouds = [c for s in scans if (c := load_points(api, pid, s, Path(d))) is not None and len(c)]
    if not clouds:
        raise ValueError("the scans have no points to fit to yet")
    pts = np.concatenate(clouds)
    api.job(job["id"], stage="fitting", progress=0.4)
    read = api.model(pid)
    ops, fitted, skipped = fit_model(read, ids, pts)
    seq = int(read.get("seq") or 0)
    if ops:
        api.job(job["id"], stage="saving", progress=0.85)
        for attempt in range(2):
            try:
                seq = int(api.model_ops(pid, ops, note="Fit to scan", author=author)["seq"])
                break
            except Exception as e:  # a 409: someone changed some of them meanwhile
                status = getattr(e, "status", None)
                body = getattr(e, "body", "")
                if status != 409 or attempt:
                    raise
                import json as _json

                stale = {c["id"] for c in (_json.loads(body).get("conflicts") or [])}
                ops = [o for o in ops if o["id"] not in stale]
                fitted = [f for f in fitted if f["id"] not in stale]
                skipped += [{"id": i, "reason": "changed meanwhile"} for i in sorted(stale)]
                if not ops:
                    break
    return {"fitted": fitted, "skipped": skipped, "seq": seq}
