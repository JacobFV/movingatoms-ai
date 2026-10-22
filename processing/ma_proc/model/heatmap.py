"""The `heatmap` job (§9, §11): how far every scan point is from the model.

For each ready scan with a viewer layer, every point's distance to the nearest model surface (exact point-to-triangle,
over a model subdivided to ≤ 0.25 m triangles, candidates from a KD-tree of triangle centroids), and the kind group of
that nearest element when it's within 100 mm. Written in the attribute format web/src/viewer/heatAttr.ts reads:
3-byte records in the layer's octree order (uint16 deviation in 0.1 mm, 65535 = nothing within 1 m; a class byte
with the group in bits 0–2), in immutable pages named by content, an index.json naming them, and distances.json with
the histograms the legend reads (heatStats.ts). Keys are relative to projects/<pid>/ (the viewer's assetBase).

input: {revision?: number} a checkpoint (its graph.json), or {live: true} the live model; {scan_id?} one scan.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from .build import mesh_loader
from .geometry import Model, all_parts
from .points import load_layer, ready_scans

ATTR_SCHEMA = "ma-heat-attr/1"
NONE = 0xFFFF
REACH_M = 1.0
NEAR_M = 0.1
PAGE_POINTS = 1 << 20
MAX_EDGE = 0.25
K = 12

# heatStats.ts HEAT_CATEGORIES: 1 floor/ground, 2 structure, 3 steel, 4 pipe/duct, 5 equipment, 6 objects, 0 unexplained
CATEGORY_NAMES = {1: "floor/ground", 2: "structure", 3: "steel", 4: "pipe/duct", 5: "equipment", 6: "objects", 0: "unexplained", 7: "marked"}
EDGES_MM: list[float | None] = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 150, 200, 300, 500, 1000, None]


def category(e: dict) -> int:
    kind = e.get("kind")
    if kind == "slab":
        return 1 if (e.get("params") or {}).get("role") not in ("ceiling", "roof") else 2
    if kind in ("wall", "column", "stair", "roof", "curtain_wall"):
        return 2
    if kind in ("beam", "railing"):
        return 3
    if kind in ("pipe", "duct", "pipe_fitting", "duct_fitting", "valve", "cable_tray"):
        return 4
    if kind == "equipment":
        return 5
    return 6


def subdivide(tri: np.ndarray, owner: np.ndarray, max_edge: float = MAX_EDGE) -> tuple[np.ndarray, np.ndarray]:
    """Split triangles at their longest edge until every edge is ≤ max_edge."""
    out_t, out_o = [], []
    while len(tri):
        e = np.stack([np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1), np.linalg.norm(tri[:, 2] - tri[:, 1], axis=1), np.linalg.norm(tri[:, 0] - tri[:, 2], axis=1)], axis=1)
        big = e.max(axis=1) > max_edge
        out_t.append(tri[~big])
        out_o.append(owner[~big])
        tri, owner, e = tri[big], owner[big], e[big]
        if not len(tri):
            break
        k = e.argmax(axis=1)  # split edge k: (k, k+1)
        i0 = k
        i1 = (k + 1) % 3
        i2 = (k + 2) % 3
        r = np.arange(len(tri))
        a, b, c = tri[r, i0], tri[r, i1], tri[r, i2]
        mid = (a + b) / 2
        tri = np.concatenate([np.stack([a, mid, c], 1), np.stack([mid, b, c], 1)])
        owner = np.concatenate([owner, owner])
    return np.concatenate(out_t) if out_t else np.zeros((0, 3, 3)), np.concatenate(out_o) if out_o else np.zeros(0, dtype=np.int64)


def point_triangle_distance(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Exact distances from points p[i] to triangles (a[i], b[i], c[i]) (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b
    d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c
    d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    with np.errstate(divide="ignore", invalid="ignore"):
        denom = 1.0 / (va + vb + vc)
        v = vb * denom
        w = vc * denom
        q = a + ab * v[..., None] + ac * w[..., None]  # inside the face
        t_ab = d1 / (d1 - d3)
        t_ac = d2 / (d2 - d6)
        t_bc = (d4 - d3) / ((d4 - d3) + (d5 - d6))
    cases = [
        ((d1 <= 0) & (d2 <= 0), a),
        ((d3 >= 0) & (d4 <= d3), b),
        ((d6 >= 0) & (d5 <= d6), c),
        ((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + ab * t_ab[..., None]),
        ((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + ac * t_ac[..., None]),
        ((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + (c - b) * t_bc[..., None]),
    ]
    done = np.zeros(p.shape[:-1], dtype=bool)
    for cond, val in cases:
        sel = cond & ~done
        q = np.where(sel[..., None], val, q)
        done |= sel
    q = np.nan_to_num(q, nan=np.inf)
    return np.linalg.norm(p - q, axis=-1)


class Surfaces:
    """The model's surfaces, ready for nearest-surface queries."""

    def __init__(self, read: dict, load_mesh=None):
        m = Model(read)
        parts = all_parts(m, load_mesh)
        ids = list(parts)
        tris, owners = [], []
        for i, id in enumerate(ids):
            for p in parts[id]:
                t = p.triangles
                tris.append(t)
                owners.append(np.full(len(t), i, dtype=np.int64))
        self.ids = ids
        self.categories = np.array([category(m.elements[id]) for id in ids] + [0], dtype=np.uint8)
        if tris:
            self.tri, self.owner = subdivide(np.concatenate(tris), np.concatenate(owners))
        else:
            self.tri, self.owner = np.zeros((0, 3, 3)), np.zeros(0, dtype=np.int64)
        self.tree = cKDTree(self.tri.mean(axis=1)) if len(self.tri) else None

    def query(self, pts: np.ndarray, chunk: int = 200_000) -> tuple[np.ndarray, np.ndarray]:
        """(distance m, nearest element index or -1) per point; np.inf beyond REACH_M."""
        n = len(pts)
        dist = np.full(n, np.inf)
        owner = np.full(n, -1, dtype=np.int64)
        if self.tree is None or not n:
            return dist, owner
        k = min(K, len(self.tri))
        reach = REACH_M + MAX_EDGE  # a centroid is at most ~edge/√3 from its triangle's farthest point
        for s in range(0, n, chunk):
            p = pts[s : s + chunk]
            _, idx = self.tree.query(p, k=k, distance_upper_bound=reach)
            idx = idx.reshape(len(p), k)
            valid = idx < len(self.tri)
            safe = np.where(valid, idx, 0)
            t = self.tri[safe]  # (m, k, 3, 3)
            d = point_triangle_distance(np.repeat(p[:, None, :], k, axis=1), t[:, :, 0], t[:, :, 1], t[:, :, 2])
            d = np.where(valid, d, np.inf)
            j = d.argmin(axis=1)
            best = d[np.arange(len(p)), j]
            dist[s : s + chunk] = np.where(best <= REACH_M, best, np.inf)
            owner[s : s + chunk] = np.where(best <= REACH_M, self.owner[safe[np.arange(len(p)), j]], -1)
        return dist, owner


def encode(dist: np.ndarray, cats: np.ndarray) -> bytes:
    """3-byte records: uint16 deviation in 0.1 mm (65535: nothing within 1 m), then the category byte."""
    q = np.where(np.isfinite(dist), np.clip(np.round(dist * 1e4), 0, NONE - 1), NONE).astype("<u2")
    rec = np.empty((len(dist), 3), dtype=np.uint8)
    rec[:, :2] = q.view(np.uint8).reshape(-1, 2)
    rec[:, 2] = cats & 7
    return rec.tobytes()


def histograms(dist: np.ndarray, cats: np.ndarray) -> dict:
    mm = dist * 1000
    edges = np.array([e if e is not None else np.inf for e in EDGES_MM], dtype=float)

    def hist(x: np.ndarray) -> list[int]:
        return np.histogram(np.where(np.isfinite(x), x, 1e12), bins=edges)[0].astype(int).tolist()

    by = {CATEGORY_NAMES[c]: hist(mm[cats == c]) for c in range(7) if (cats == c).any()}
    return {"edges_mm": EDGES_MM, "points": int(len(dist)), "all": hist(mm), "by_category": by, "reach_mm": REACH_M * 1000}


def heat_stats(dist: np.ndarray, cats: np.ndarray) -> dict:
    near = dist <= NEAR_M
    explained = cats != 0
    d = dist[near] * 1000
    by = {CATEGORY_NAMES[c]: int((cats == c).sum()) for c in range(7) if (cats == c).any()}
    return {
        "points": int(len(dist)),
        "p50_mm": round(float(np.percentile(d, 50)), 1) if len(d) else None,
        "p95_mm": round(float(np.percentile(d, 95)), 1) if len(d) else None,
        "within_25mm_pct": round(100 * float((dist[explained] <= 0.025).mean()), 1) if explained.any() else None,
        "points_near_model_pct": round(100 * float(near.mean()), 1) if len(dist) else 0.0,
        "by_category": by,
    }


def compute(surfaces: Surfaces, pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dist, owner = surfaces.query(pts)
    cats = np.where((owner >= 0) & (dist <= NEAR_M), surfaces.categories[owner], 0).astype(np.uint8)
    return dist, cats


def write_attr(api: Any, pid: str, layer_key_rel: str, base_rel: str, data: bytes, points: int, octree_bpp: int) -> dict:
    """Upload the pages and the index; returns the index (keys relative to projects/<pid>/)."""
    B = 3
    pages = []
    for i in range(0, points, PAGE_POINTS):
        chunk = data[i * B : min(points, i + PAGE_POINTS) * B]
        name = f"p{i // PAGE_POINTS:05d}-{hashlib.sha256(chunk).hexdigest()[:16]}.bin"
        key = f"projects/{pid}/{base_rel}{name}"
        if not api.exists(key):
            api.upload_bytes(chunk, key)
        pages.append(name)
    index = {"schema": ATTR_SCHEMA, "base": base_rel, "layer": layer_key_rel, "points": points, "octree_bytes_per_point": octree_bpp,
             "page_points": PAGE_POINTS, "bytes_per_point": B, "pages": pages}
    return index


def run(api: Any, job: dict, claim: dict) -> dict:
    pid = job["project_id"]
    inp = job.get("input") or {}
    rel = lambda k: k[len(f"projects/{pid}/"):] if k.startswith(f"projects/{pid}/") else k  # noqa: E731
    proj = api.project(pid)
    scans = ready_scans(proj.get("scans") or claim.get("scans") or [], inp.get("scan_id"))
    if not scans:
        raise ValueError("no ready scan to measure")
    number = inp.get("revision")
    revision = None
    if number:
        revision = next((r for r in proj.get("revisions") or [] if r["number"] == int(number)), None)
        if not revision or not revision.get("graph_key"):
            raise ValueError(f"revision {number} has no model to measure")
    api.job(job["id"], stage="reading the model", progress=0.05)
    with tempfile.TemporaryDirectory() as d:
        if revision:
            read = json.loads(api.download(revision["graph_key"], Path(d) / "graph.json").read_text())
            tag = f"r{revision['number']}"
        else:
            read = api.model(pid)
            tag = f"live-{int(read.get('seq') or 0)}"
        seq = int(read.get("seq") or 0)
        surfaces = Surfaces(read, mesh_loader(api, pid))
        heatmaps = dict((revision or {}).get("heatmaps") or {})
        if revision:
            for s in scans:
                heatmaps[s["id"]] = {"status": "computing"}
            api.update_revision(pid, revision["number"], heatmaps=heatmaps)
        results = {}
        for i, scan in enumerate(scans):
            api.job(job["id"], stage=f"measuring {scan.get('name') or 'the scan'}", progress=0.1 + 0.8 * i / len(scans))
            layer = load_layer(api, pid, scan, Path(d))
            if layer is None:
                continue
            dist, cats = compute(surfaces, layer.xyz)
            base_rel = f"heatmaps/{scan['id']}/{tag}/"
            index = write_attr(api, pid, rel(layer.metadata_key), base_rel, encode(dist, cats), len(layer.xyz), layer.bytes_per_point)
            index_key = api.upload_json(index, f"projects/{pid}/{base_rel}index.json")
            dist_key = api.upload_json(histograms(dist, cats), f"projects/{pid}/{base_rel}distances.json")
            stats = {**heat_stats(dist, cats), "distances_key": rel(dist_key)}
            entry = {"status": "ready", "format": "attr", "potree": None, "layer": rel(layer.metadata_key), "attr": rel(index_key),
                     "mode": "full", "seq": seq, "updated_at": datetime.now(timezone.utc).isoformat(), "stats": stats}
            heatmaps[scan["id"]] = entry
            results[scan["id"]] = entry
        if not results:
            raise ValueError("the ready scans have no viewer layer to measure")
        if revision:
            latest = {**next(iter(results.values())), "scan_id": next(iter(results))}
            api.update_revision(pid, revision["number"], heatmaps=heatmaps, heatmap=latest)
        else:
            # the live heatmap: stored on the project (the manifest serves projects.settings.live_heatmaps), then announced
            for sid, entry in results.items():
                try:
                    api.set_live_heatmap(pid, sid, entry)
                except Exception as e:  # noqa: BLE001 - a server without the route: the files are written, the event still goes
                    if getattr(e, "status", None) != 404:
                        raise
            api.events(pid, {"type": "job.updated", "id": job["id"], "type_": "heatmap_live", "status": "done", "stage": None, "progress": 1})
    api.job(job["id"], stage="done", progress=1.0)
    return {"revision": revision["number"] if revision else None, "live": not revision, "seq": seq, "heatmaps": results}
