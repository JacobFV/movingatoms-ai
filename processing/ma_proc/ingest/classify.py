"""Point labels, scheme ma-v1 (types.ts LABELS): which part of a building each point is.

Geometric classification on a sample of the scan, then propagated to every point by nearest neighbour:
  1. noise          statistical outliers (mean k-NN distance far above the local norm)
  2. floor/ceiling  horizontal surfaces at the measured floor and ceiling heights
  3. walls          large vertical planes: vertical-planar points grouped by facing direction, connected in a 10 cm
                    voxel grid, kept when tall and long enough for a wall
  4. objects        what's left, as connected components in the voxel grid, each judged by its shape:
                    columns (floor-to-ceiling, small footprint), beams (linear, against the ceiling), pipes and ducts
                    (cylinder / box fits on 0.6 m blocks along elongated runs), stairs and railings (stepped
                    horizontal treads, thin rails at hand height), equipment (large solid objects), furniture/clutter
  5. outside        points beyond the building envelope (outside the filled floor footprint, under the lowest floor)
  6. smoothing      a k-NN majority vote removes speckle
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_closing, binary_dilation, binary_fill_holes
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from .features import Features

UNCLASSIFIED, FLOOR, CEILING, WALL, COLUMN, BEAM, PIPE, DUCT, EQUIPMENT, STAIR, OPENING, CLUTTER, OUTSIDE, NOISE = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 18)
NAMES = {0: "Unclassified", 1: "Floor", 2: "Ceiling", 3: "Wall", 4: "Column", 5: "Beam / structure", 6: "Pipe", 7: "Duct",
         8: "Equipment", 9: "Stair / railing", 10: "Opening", 11: "Furniture / clutter", 12: "Outside", 18: "Noise"}
METHOD = "geometric: k-NN eigen-features, plane grouping, voxel components, cylinder fits (ma-proc)"

_HALF26 = np.array([(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dy, dz) > (0, 0, 0)])


def voxel_components(vox: np.ndarray) -> np.ndarray:
    """Connected components (26-neighbourhood) of unique integer voxels; returns a component id per voxel."""
    m = len(vox)
    if m == 0:
        return np.zeros(0, np.int64)
    v = vox - vox.min(axis=0) + 1
    dims = v.max(axis=0) + 2
    lin = (v[:, 0] * dims[1] + v[:, 1]) * dims[2] + v[:, 2]
    order = np.argsort(lin)
    slin = lin[order]
    rows, cols = [], []
    for d in _HALF26:
        nl = lin + (d[0] * dims[1] + d[1]) * dims[2] + d[2]
        pos = np.minimum(np.searchsorted(slin, nl), m - 1)
        hit = slin[pos] == nl
        rows.append(np.nonzero(hit)[0])
        cols.append(order[pos[hit]])
    r = np.concatenate(rows)
    c = np.concatenate(cols)
    g = coo_matrix((np.ones(len(r), np.int8), (r, c)), shape=(m, m))
    return connected_components(g, directed=False)[1]


def point_components(xyz: np.ndarray, size: float) -> np.ndarray:
    """A component id per point: points grouped by connected voxels."""
    keys = np.floor(xyz / size).astype(np.int64)
    vox, inv = np.unique(keys, axis=0, return_inverse=True)
    return voxel_components(vox)[inv.ravel()]


def groups(ids: np.ndarray):
    """(id, point indices) for every id, largest first."""
    order = np.argsort(ids, kind="stable")
    sids = ids[order]
    cuts = np.flatnonzero(np.diff(sids)) + 1
    parts = np.split(order, cuts)
    parts.sort(key=len, reverse=True)
    return parts


def fit_circle(p2: np.ndarray) -> tuple[float, float]:
    """Kasa algebraic circle fit in 2D: (radius, rms residual)."""
    x, y = p2[:, 0], p2[:, 1]
    a = np.column_stack([2 * x, 2 * y, np.ones(len(x))])
    b = x * x + y * y
    try:
        c, *_ = np.linalg.lstsq(a, b, rcond=None)
    except np.linalg.LinAlgError:
        return float("inf"), float("inf")
    cx, cy = c[0], c[1]
    r2 = c[2] + cx * cx + cy * cy
    if r2 <= 0:
        return float("inf"), float("inf")
    r = float(np.sqrt(r2))
    res = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
    return r, float(np.sqrt(np.mean(res * res)))


def _pca(p: np.ndarray):
    c = p - p.mean(axis=0)
    w, v = np.linalg.eigh(c.T @ c / max(1, len(p)))
    return w[::-1], v[:, ::-1]  # descending


class Levels:
    """For any height, the floor below and the ceiling above it (the room it's in)."""

    def __init__(self, levels: list[dict], zmin: float, zmax: float):
        self.floors = sorted(l["z"] for l in levels if l["kind"] == "floor") or [zmin]
        self.ceilings = sorted(l["z"] for l in levels if l["kind"] == "ceiling")
        self.zmax = zmax

    def floor_below(self, z: np.ndarray) -> np.ndarray:
        f = np.array(self.floors)
        i = np.clip(np.searchsorted(f, z + 0.3, side="right") - 1, 0, len(f) - 1)
        return f[i]

    def ceiling_above(self, z: np.ndarray) -> np.ndarray:
        if not self.ceilings:
            return np.full(np.shape(z), self.zmax)
        c = np.array(self.ceilings)
        i = np.searchsorted(c, z - 0.3, side="left")
        out = np.where(i < len(c), c[np.minimum(i, len(c) - 1)], self.zmax)
        return out


def classify(f: Features, levels: list[dict], progress=lambda frac, text: None) -> np.ndarray:
    xyz = f.xyz
    n = len(xyz)
    lab = np.zeros(n, np.uint8)
    z = xyz[:, 2]
    L = Levels(levels, float(z.min()), float(z.max()))
    nz = f.nz

    # 1. noise: statistical outliers
    progress(0.05, "Removing noise")
    # a point much further from its neighbours than they are from theirs (local, so sparse far-away surfaces are kept)
    kd = f.knn_dist
    _, nb = f.tree.query(xyz, k=9, workers=-1)
    local = np.median(kd[nb[:, 1:]], axis=1)
    lab[(kd > 4.0 * local) & (kd > 2.0 * np.median(kd))] = NOISE

    # 2. floors and ceilings
    progress(0.15, "Labelling floors and ceilings")
    free = lab == 0
    horiz = nz > 0.85
    for zf in L.floors:
        lab[free & (((np.abs(z - zf) < 0.07) & horiz) | (np.abs(z - zf) < 0.03))] = FLOOR
    free = lab == 0
    for zc in L.ceilings:
        lab[free & (np.abs(z - zc) < 0.10) & (horiz | (np.abs(z - zc) < 0.04))] = CEILING
    # ramps and uneven slabs: the near-horizontal surface connected to a floor or ceiling band is part of it
    _grow_surfaces(xyz, f, lab, L)

    # 3. walls: vertical planes, grouped by facing direction and connectivity
    progress(0.3, "Labelling walls")
    free = lab == 0
    cand = free & (nz < 0.3) & (f.planarity > 0.35)
    az = np.degrees(np.arctan2(f.normal[:, 1], f.normal[:, 0])) % 180.0
    room_h = np.maximum(1.0, L.ceiling_above(z) - L.floor_below(z))
    for b in range(12):
        lo = b * 15.0 - 7.5
        win = cand & (lab == 0) & ((((az - lo) % 180.0)) < 30.0)
        idx = np.flatnonzero(win)
        if len(idx) < 100:
            continue
        comp = point_components(xyz[idx], 0.10)
        for g in groups(comp):
            if len(g) < 150:
                break
            pts = xyz[idx[g]]
            hspan = float(pts[:, 2].max() - pts[:, 2].min())
            w2, v2 = _pca(pts[:, :2])
            along = pts[:, :2] @ v2[:, 0]
            length = float(along.max() - along.min())
            thick = float(np.sqrt(max(w2[1], 0)))
            need_h = max(1.2, 0.5 * float(np.median(room_h[idx[g]])))
            if hspan >= need_h and length >= 0.6 and thick < 0.12:
                lab[idx[g]] = WALL

    # 4. pipes and ducts first (they tie equipment together into one blob), then objects from what's left
    progress(0.5, "Finding pipes and ducts")
    _runs(xyz, f, lab, L)
    progress(0.65, "Labelling columns, beams and equipment")
    rest = np.flatnonzero(lab == 0)
    if len(rest):
        comp = point_components(xyz[rest], 0.10)
        for g in groups(comp):
            ids = rest[g]
            if len(g) < 25:
                lab[ids] = CLUTTER
                continue
            lab[ids] = _object(xyz[ids], f, ids, L)

    # 5. outside the building envelope
    progress(0.85, "Separating the outside")
    floor_pts = xyz[(lab == FLOOR) | (lab == CEILING), :2]
    if len(floor_pts) > 500:
        cell = 0.25
        lo = np.floor(xyz[:, :2].min(axis=0) / cell).astype(np.int64) - 4
        k = np.floor(xyz[:, :2] / cell).astype(np.int64) - lo
        shape = tuple(k.max(axis=0) + 5)
        if shape[0] * shape[1] < 60_000_000:
            occ = np.zeros(shape, bool)
            fk = np.floor(floor_pts / cell).astype(np.int64) - lo
            occ[fk[:, 0], fk[:, 1]] = True
            occ = binary_fill_holes(binary_closing(occ, iterations=4))
            occ = binary_dilation(occ, iterations=3)
            out = ~occ[k[:, 0], k[:, 1]]
            lab[out & (lab != NOISE)] = OUTSIDE
    lab[(z < min(L.floors) - 0.4) & (lab != NOISE)] = OUTSIDE

    # 6. smoothing
    progress(0.95, "Cleaning up the labels")
    return smooth(f, lab)


def _grow_surfaces(xyz: np.ndarray, f: Features, lab: np.ndarray, L: Levels) -> None:
    flat = ((lab == 0) | (lab == FLOOR) | (lab == CEILING)) & (f.nz > 0.97) & (f.planarity > 0.3)
    idx = np.flatnonzero(flat)
    if len(idx) < 100:
        return
    comp = point_components(xyz[idx], 0.15)
    for g in groups(comp):
        if len(g) < 200:
            break
        ids = idx[g]
        cur = lab[ids]
        nf, nc = int((cur == FLOOR).sum()), int((cur == CEILING).sum())
        seed = max(nf, nc)
        if seed < 0.2 * len(g):
            continue  # not part of a floor or ceiling (a table top, a car roof)
        lab[ids[cur == 0]] = FLOOR if nf >= nc else CEILING


def _object(p: np.ndarray, f: Features, ids: np.ndarray, L: Levels) -> int:
    zmin, zmax = float(p[:, 2].min()), float(p[:, 2].max())
    fl = float(L.floor_below(np.array([zmin]))[0])
    ce = float(L.ceiling_above(np.array([zmax]))[0])
    room = max(1.5, ce - fl)
    ez = zmax - zmin
    w2, v2 = _pca(p[:, :2])
    a = p[:, :2] @ v2
    ex = float(np.ptp(a[:, 0]))
    ey = float(np.ptp(a[:, 1]))
    # column: floor to ceiling, small footprint
    if max(ex, ey) <= 1.0 and ez >= 0.7 * room and zmin - fl < 0.5 and (ce - zmax < 0.5 or not L.ceilings):
        return COLUMN
    w3, v3 = _pca(p)
    elong = w3[0] / max(w3[1], 1e-9)
    horizontal_axis = abs(v3[2, 0]) < 0.3
    cross = 2 * np.sqrt(max(w3[1], 0))
    # beam: a long horizontal member against the ceiling
    if L.ceilings and ce - zmax < 0.25 and zmin > ce - 1.2 and horizontal_axis and elong > 6 and max(ex, ey) > 1.5 and cross < 0.8:
        return BEAM
    # railing: thin, long, at hand height
    if horizontal_axis and elong > 12 and cross < 0.12 and 0.6 < zmax - fl < 1.4 and max(ex, ey) > 1.0:
        return STAIR
    # stairs: three or more horizontal treads at regular rises, each one a going further on in the same direction
    if _is_stair(p, f.nz[ids] > 0.92, f.planarity[ids] > 0.5):
        return STAIR
    # equipment: big solid things; the rest is furniture and clutter
    if ez >= 0.6 and ex * ey * ez >= 0.3 and len(p) >= 200:
        return EQUIPMENT
    return CLUTTER


def ransac_circle(p2: np.ndarray, tries: int = 256, seed: int = 3) -> tuple[float, np.ndarray, np.ndarray]:
    """Robust circle in 2D: (radius, centre, inlier mask). Vectorised RANSAC over point triplets, refined by Kasa."""
    n = len(p2)
    if n < 12:
        return float("inf"), np.zeros(2), np.zeros(n, bool)
    rng = np.random.default_rng(seed)
    t = rng.integers(0, n, size=(tries, 3))
    a, b, c = p2[t[:, 0]], p2[t[:, 1]], p2[t[:, 2]]
    d = 2 * (a[:, 0] * (b[:, 1] - c[:, 1]) + b[:, 0] * (c[:, 1] - a[:, 1]) + c[:, 0] * (a[:, 1] - b[:, 1]))
    ok = np.abs(d) > 1e-12
    a2, b2, c2 = (a * a).sum(1), (b * b).sum(1), (c * c).sum(1)
    ux = np.where(ok, (a2 * (b[:, 1] - c[:, 1]) + b2 * (c[:, 1] - a[:, 1]) + c2 * (a[:, 1] - b[:, 1])) / np.where(ok, d, 1), np.inf)
    uy = np.where(ok, (a2 * (c[:, 0] - b[:, 0]) + b2 * (a[:, 0] - c[:, 0]) + c2 * (b[:, 0] - a[:, 0])) / np.where(ok, d, 1), np.inf)
    cen = np.column_stack([ux, uy])
    r = np.sqrt(((a - cen) ** 2).sum(1))
    good = ok & (r > 0.012) & (r < 0.45)
    if not good.any():
        return float("inf"), np.zeros(2), np.zeros(n, bool)
    cen, r = cen[good], r[good]
    sub = p2 if n <= 3000 else p2[rng.choice(n, 3000, replace=False)]
    dist = np.abs(np.sqrt(((sub[None, :, :] - cen[:, None, :]) ** 2).sum(-1)) - r[:, None])
    tol = (0.006 + 0.06 * r)[:, None]
    best = int(np.argmax((dist < tol).sum(1)))
    c0, r0 = cen[best], r[best]
    inl = np.abs(np.sqrt(((p2 - c0) ** 2).sum(1)) - r0) < 0.006 + 0.06 * r0
    if inl.sum() >= 12:  # refine on the inliers
        q = p2[inl]
        A = np.column_stack([2 * q[:, 0], 2 * q[:, 1], np.ones(len(q))])
        sol, *_ = np.linalg.lstsq(A, (q * q).sum(1), rcond=None)
        rr = sol[2] + sol[0] ** 2 + sol[1] ** 2
        if rr > 0:
            c0, r0 = sol[:2], float(np.sqrt(rr))
            inl = np.abs(np.sqrt(((p2 - c0) ** 2).sum(1)) - r0) < 0.006 + 0.06 * r0
    return float(r0), c0, inl


def _is_stair(p: np.ndarray, horiz: np.ndarray, planar: np.ndarray) -> bool:
    tread = horiz & planar
    if tread.sum() < 60 or np.ptp(p[:, 2]) < 0.4:
        return False
    tz = p[tread, 2]
    hist, edges = np.histogram(tz, bins=np.arange(tz.min(), tz.max() + 0.03, 0.02))
    peaks = [i for i in range(len(hist)) if hist[i] >= max(10, 0.04 * tread.sum()) and hist[i] == hist[max(0, i - 3) : i + 4].max()]
    if len(peaks) < 3:
        return False
    zs = np.array([(edges[i] + edges[i + 1]) / 2 for i in peaks])
    rises = np.diff(zs)
    if not (0.12 <= np.median(rises) <= 0.23) or np.ptp(rises) > 0.08:
        return False
    cents = np.array([p[tread & (np.abs(p[:, 2] - z) < 0.02), :2].mean(axis=0) for z in zs])
    steps = np.diff(cents, axis=0)
    goings = np.linalg.norm(steps, axis=1)
    if not ((goings > 0.18) & (goings < 0.45)).all():
        return False
    dirs = steps / goings[:, None]
    return bool((dirs @ dirs.mean(axis=0) > 0.85).all())


def _runs(xyz: np.ndarray, f: Features, lab: np.ndarray, L: Levels, block: float = 0.5) -> None:
    # two passes, the second on a grid shifted by half a block, so a pipe cut by a block edge is found whole
    rad = np.zeros(len(lab), np.float32)
    _runs_pass(xyz, f, lab, L, block, 0.0, rad)
    _runs_pass(xyz, f, lab, L, block, block / 2, rad)
    # a pipe is a run: short fat cylinders (motor housings, tanks, drums) go back to the objects pass. Judged per
    # radius class, so a riser touching a motor housing isn't taken for part of it.
    pipe = np.flatnonzero(lab == PIPE)
    if len(pipe):
        cls = np.digitize(rad[pipe], [0.06, 0.12, 0.2])
        for c in np.unique(cls):
            sel = pipe[cls == c]
            comp = point_components(xyz[sel], 0.08)
            for g in groups(comp):
                ids = sel[g]
                r = float(np.median(rad[ids]))
                if len(g) < 30:
                    lab[ids] = 0
                    continue
                w3, v3 = _pca(xyz[ids])
                length = float(np.ptp(xyz[ids] @ v3[:, 0]))
                if length < max(0.5, 5.0 * r):
                    lab[ids] = 0
                    continue
                # a thick vertical cylinder standing floor to ceiling is a round column
                zz = xyz[ids, 2]
                fl = float(L.floor_below(np.array([zz.min()]))[0])
                ce = float(L.ceiling_above(np.array([zz.max()]))[0])
                if abs(v3[2, 0]) > 0.9 and r >= 0.1 and np.ptp(zz) >= 0.5 * max(1.5, ce - fl):
                    lab[ids] = COLUMN


def _runs_pass(xyz: np.ndarray, f: Features, lab: np.ndarray, L: Levels, block: float, shift: float, rad: np.ndarray) -> None:
    """Pipes and ducts on 0.5 m blocks of unlabelled points. A pipe's surface normals all lie across its axis, so the
    axis is the direction the normals don't vary in (the smallest eigenvector of their scatter); the points projected
    along it fit a circle (RANSAC, radius 12 mm – 450 mm) whose inliers face the centre. Up to three pipes per block.
    A duct: an elongated block overhead whose cross-section is a box of flat faces."""
    cand = np.flatnonzero(lab == 0)
    if not len(cand):
        return
    keys = np.floor((xyz[cand] + shift) / block).astype(np.int64)
    _, inv = np.unique(keys, axis=0, return_inverse=True)
    for g in groups(inv.ravel()):
        if len(g) < 60:
            break
        remaining = cand[g]
        for _ in range(3):
            if len(remaining) < 60:
                break
            nrm = f.normal[remaining]
            w, v = np.linalg.eigh(nrm.T @ nrm / len(nrm))  # ascending
            if w[0] > 0.12 or w[1] < 0.05:
                break  # normals don't wrap around an axis: no cylinder here
            axis = v[:, 0]
            u = np.cross(axis, [0.0, 0.0, 1.0] if abs(axis[2]) < 0.9 else [1.0, 0.0, 0.0])
            u /= np.linalg.norm(u)
            t = np.cross(axis, u)
            p = xyz[remaining]
            p2 = np.column_stack([p @ u, p @ t])
            r, c, inl = ransac_circle(p2)
            if not np.isfinite(r) or inl.sum() < max(40, 0.25 * len(remaining)):
                break
            # inliers' normals must point at the centre (a cylinder, not a flat face crossing the circle)
            radial = p2[inl] - c
            radial /= np.maximum(np.linalg.norm(radial, axis=1, keepdims=True), 1e-9)
            n2 = np.column_stack([nrm[inl] @ u, nrm[inl] @ t])
            n2 /= np.maximum(np.linalg.norm(n2, axis=1, keepdims=True), 1e-9)
            if np.median(np.abs((radial * n2).sum(1))) < 0.9:
                break
            # a curved surface: the inliers' normals sweep round the axis (flat faces give one or two directions)
            ang = np.degrees(np.arctan2(n2[:, 1], n2[:, 0])) % 180.0
            occupied = np.bincount((ang // 10).astype(int), minlength=18) >= max(3, 0.01 * len(ang))
            if occupied.sum() < 5:
                break
            # and run along the axis for at least a pipe's diameter
            along = p[inl] @ axis
            if np.ptp(along) < max(0.15, 1.5 * r):
                break
            lab[remaining[inl]] = PIPE
            rad[remaining[inl]] = r
            remaining = remaining[~inl]
        if len(remaining) >= 60 and (lab[remaining] == 0).all():
            p = xyz[remaining]
            w3, v3 = _pca(p)
            if w3[0] / max(w3[1], 1e-9) >= 3.0 and abs(v3[2, 0]) < 0.3:
                ax = v3[:, 0]
                span = np.ptp(np.column_stack([p @ v3[:, 1], p @ v3[:, 2]]), axis=0)
                zfl = float(L.floor_below(np.array([p[:, 2].min()]))[0])
                if span.min() >= 0.12 and span.max() <= 1.6 and float(np.mean(f.planarity[remaining])) > 0.6 and p[:, 2].min() - zfl > 1.8:
                    lab[remaining] = DUCT


def smooth(f: Features, lab: np.ndarray, k: int = 10) -> np.ndarray:
    """Majority vote over each point's neighbours, for points whose own label is a minority there."""
    n = len(lab)
    out = lab.copy()
    for s in range(0, n, 500_000):
        e = min(n, s + 500_000)
        _, idx = f.tree.query(f.xyz[s:e], k=k + 1, workers=-1)
        nb = lab[idx[:, 1:]]
        counts = np.zeros((e - s, 19), np.int16)
        rows = np.repeat(np.arange(e - s), k)
        np.add.at(counts, (rows, nb.ravel()), 1)
        own = counts[np.arange(e - s), lab[s:e]]
        best = counts.argmax(axis=1)
        flip = (own <= 2) & (counts[np.arange(e - s), best] >= 6) & (lab[s:e] != NOISE)
        out[s:e][flip] = best[flip]
    return out


def counts(lab: np.ndarray) -> dict[str, int]:
    """Points per label code, keyed by the code as a string (as the app reads Scan.labels.counts)."""
    vals, cnt = np.unique(lab, return_counts=True)
    return {str(int(v)): int(c) for v, c in zip(vals, cnt)}


def names() -> dict[str, str]:
    return {str(k): v for k, v in NAMES.items()}
