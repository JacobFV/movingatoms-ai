"""What a scan is: its working frame (metres, Z up, offset near the origin), bounds, floor and ceiling levels,
footprint and point density — the scan's brief (types.ts Brief), which the estimate prices from."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

from . import features as F
from .store import PointStore

SAMPLE = 2_000_000


@dataclass
class Frame:
    """source → working: rotate (Y-up files to Z-up), then subtract the offset."""
    offset: np.ndarray
    y_up: bool = False
    note: str | None = None

    def apply(self, xyz: np.ndarray) -> np.ndarray:
        p = np.asarray(xyz, dtype=np.float64)
        if self.y_up:
            p = np.column_stack([p[:, 0], -p[:, 2], p[:, 1]])
        return p - self.offset

    def to_json(self, crs: str | None) -> dict:
        out = {"units": "m", "up": "z", "offset": [round(float(v), 6) for v in self.offset]}
        if crs:
            out["source_crs"] = crs
        notes = ["working frame = source − offset" + ("; the source was Y-up and was turned Z-up" if self.y_up else "")]
        if self.note:
            notes.append(self.note)
        out["note"] = ". ".join(notes)
        return out


@dataclass
class Measured:
    frame: Frame
    bounds: dict  # working frame
    extent: list[float]
    footprint_m2: float
    levels: list[dict]  # [{z, kind}]
    spacing_mm: float
    sample_idx: np.ndarray
    feats: F.Features  # the sample's features, working frame
    warnings: list[str] = field(default_factory=list)


def _raw_bounds(store: PointStore) -> tuple[np.ndarray, np.ndarray]:
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    xyz = store.xyz
    for s, e in store.chunks():
        c = xyz[s:e]
        lo = np.minimum(lo, c.min(axis=0))
        hi = np.maximum(hi, c.max(axis=0))
    return lo, hi


def _is_y_up(f: F.Features) -> bool:
    planar = f.planarity > 0.6
    if planar.sum() < 1000:
        return False
    n = np.abs(f.normal[planar])
    fz = (n[:, 2] > 0.95).mean()
    fy = (n[:, 1] > 0.95).mean()
    return fy > 2.0 * fz and fy > 0.15


def levels(f: F.Features) -> list[dict]:
    """Floors and ceilings: peaks in the heights of horizontal surfaces; a floor has things above it, a ceiling below."""
    z = f.xyz[:, 2]
    horiz = (f.nz > 0.95) & (f.planarity > 0.45)
    if horiz.sum() < 200:
        return []
    zh = z[horiz]
    lo, hi = float(zh.min()), float(zh.max())
    if hi - lo < 0.05:
        return [{"z": round(lo, 3), "kind": "floor"}]
    bins = np.arange(lo - 0.05, hi + 0.07, 0.02)
    hist, edges = np.histogram(zh, bins=bins)
    sm = gaussian_filter1d(hist.astype(float), 1.5)
    peaks, props = find_peaks(sm, height=max(30.0, 0.02 * sm.max()), distance=15, prominence=0.15 * sm.max())
    xy = f.xyz[:, :2]
    out: list[dict] = []
    areas = []
    for p in peaks:
        zc = float((edges[p] + edges[p + 1]) / 2)
        band = horiz & (np.abs(z - zc) < 0.06)
        cells = np.unique(np.floor(xy[band] / 0.25).astype(np.int64), axis=0)
        areas.append(len(cells) * 0.0625)
        out.append({"z": zc, "cells": cells})
    if not out:
        return []
    biggest = max(areas)
    kept = []
    for lv, area in zip(out, areas):
        if area < max(1.5, 0.05 * biggest):
            continue
        # look just above and just below the surface, over its own footprint
        inside = _in_cells(np.floor(xy / 0.25).astype(np.int64), lv["cells"])
        dz = z - lv["z"]
        above = int((inside & (dz > 0.15) & (dz < 1.6)).sum())
        below = int((inside & (dz < -0.15) & (dz > -1.6)).sum())
        kind = "floor" if above >= below else "ceiling"
        kept.append({"z": round(lv["z"], 3), "kind": kind, "area_m2": round(area, 1)})
    kept.sort(key=lambda d: d["z"])
    # the lowest big surface is a floor and the highest a ceiling, whatever the clutter says
    if kept and len(kept) >= 2:
        kept[0]["kind"] = "floor"
        kept[-1]["kind"] = "ceiling" if kept[-1]["z"] - kept[0]["z"] > 1.8 else kept[-1]["kind"]
    return kept


def _in_cells(keys: np.ndarray, cells: np.ndarray) -> np.ndarray:
    """Vectorised membership of integer XY keys in a set of cells."""
    if not len(cells):
        return np.zeros(len(keys), bool)
    off = keys.min(axis=0)
    span = np.maximum(keys.max(axis=0), cells.max(axis=0)) - np.minimum(off, cells.min(axis=0)) + 1
    off = np.minimum(off, cells.min(axis=0))
    lin = (keys[:, 0] - off[0]) * span[1] + (keys[:, 1] - off[1])
    cl = (cells[:, 0] - off[0]) * span[1] + (cells[:, 1] - off[1])
    return np.isin(lin, cl)


def measure(store: PointStore, sample: int = SAMPLE) -> Measured:
    warnings: list[str] = []
    lo, hi = _raw_bounds(store)
    idx, voxel = store.voxel_sample(sample)
    raw = np.asarray(store.xyz[idx])
    # the frame: Y-up detection on a small sample first
    probe = F.compute(raw[:: max(1, len(raw) // 200_000)] - lo)
    y_up = _is_y_up(probe)
    pre = Frame(np.zeros(3), y_up)
    p = pre.apply(raw)
    plo = p.min(axis=0)
    # offset: whole metres, so coordinates stay readable; x/y centred, z at the lowest point
    centre = (p.min(axis=0) + p.max(axis=0)) / 2
    offset = np.array([np.floor(centre[0]), np.floor(centre[1]), np.floor(plo[2])])
    frame = Frame(offset, y_up)
    w = p - offset
    feats = F.compute(w)
    lv = levels(feats)
    # bounds over every point, in the working frame
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    wc = frame.apply(corners)
    bmin, bmax = wc.min(axis=0), wc.max(axis=0)
    extent = (bmax - bmin).tolist()
    if max(extent) > 3000:
        warnings.append("The scan is over 3 km across. If it's in millimetres or feet, tell us the units.")
        frame.note = "very large extent: check the units"
    # footprint: occupied 25 cm cells between the lowest floor and the highest ceiling (or all of it)
    zlo = min((l["z"] for l in lv), default=float(w[:, 2].min())) - 0.3
    zhi = max((l["z"] for l in lv), default=float(w[:, 2].max())) + 0.3
    band = (w[:, 2] > zlo) & (w[:, 2] < zhi)
    cells, counts = np.unique(np.floor(w[band, :2] / 0.25).astype(np.int64), axis=0, return_counts=True)
    footprint = float((counts >= 2).sum() * 0.0625)
    # spacing on the full cloud: nearest-neighbour distances of a dense random patch around the median point
    rnd = np.asarray(store.xyz[store.sample(min(store.n, 300_000), 11)])
    from scipy.spatial import cKDTree
    d, _ = cKDTree(rnd).query(rnd, k=2, workers=-1)
    spacing_mm = float(np.median(d[:, 1]) * np.sqrt(len(rnd) / max(1, store.n)) * 1000)
    if store.n < 50_000:
        warnings.append("This scan has very few points, so the model will be coarse.")
    return Measured(frame, {"min": [round(float(v), 4) for v in bmin], "max": [round(float(v), 4) for v in bmax]},
                    [round(float(v), 3) for v in extent], round(footprint, 1),
                    [{"z": l["z"], "kind": l["kind"]} for l in lv], round(spacing_mm, 2), idx, feats, warnings)
