"""Element meshes from model params, in the working frame (metres, Z up): a Python port of packages/model/src/geometry
(the TypeScript kernel the viewer draws with), close enough that builds, fits and heatmaps agree with what people see.

Differences from the TS kernel, on purpose: wall joins are approximated (a wall end that meets another wall is extended
by that wall's half thickness instead of being mitred), and hosted holes are cut by splitting the wall into boxes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import numpy as np

try:  # mapbox-earcut: fast polygon triangulation with holes
    import mapbox_earcut as _earcut
except ImportError:  # pragma: no cover
    _earcut = None

EPS = 1e-6
HOSTED = {"opening", "door", "window"}
FRAME = 0.05
JOIN_TOL = 0.05

IFC_CLASS = {
    "level": "IfcBuildingStorey", "wall": "IfcWall", "slab": "IfcSlab", "opening": "IfcOpeningElement", "door": "IfcDoor",
    "window": "IfcWindow", "column": "IfcColumn", "beam": "IfcBeam", "pipe": "IfcPipeSegment", "duct": "IfcDuctSegment",
    "pipe_fitting": "IfcPipeFitting", "valve": "IfcValve", "duct_fitting": "IfcDuctFitting", "equipment": "IfcBuildingElementProxy",
    "stair": "IfcStair", "railing": "IfcRailing", "roof": "IfcRoof", "curtain_wall": "IfcCurtainWall", "furniture": "IfcFurniture",
    "generic": "IfcBuildingElementProxy", "cable_tray": "IfcCableCarrierSegment",
}


@dataclass
class Part:
    """One drawable part of an element: `name` (body, frame, leaf, glass, insulation) and a material hint."""
    name: str
    material: str
    vertices: np.ndarray  # (N, 3) float64, working frame
    faces: np.ndarray  # (M, 3) int64, counter-clockwise seen from outside

    @property
    def triangles(self) -> np.ndarray:
        return self.vertices[self.faces]


@dataclass
class Builder:
    verts: list = field(default_factory=list)
    faces: list = field(default_factory=list)

    def add(self, v: np.ndarray, f: np.ndarray) -> None:
        base = sum(len(x) for x in self.verts)
        self.verts.append(np.asarray(v, dtype=np.float64))
        self.faces.append(np.asarray(f, dtype=np.int64) + base)

    def quad(self, a, b, c, d) -> None:
        self.add(np.array([a, b, c, d]), np.array([[0, 1, 2], [0, 2, 3]]))

    @property
    def empty(self) -> bool:
        return not self.faces

    def part(self, name: str, material: str) -> Part | None:
        if self.empty:
            return None
        return Part(name, material, np.concatenate(self.verts), np.concatenate(self.faces))


def _num(v: Any, fallback: float) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else fallback


def ring_area(ring: np.ndarray) -> float:
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def clean_ring(ring: Iterable, eps: float = 1e-6) -> np.ndarray:
    out: list[tuple[float, float]] = []
    for p in ring or []:
        try:
            x, y = float(p[0]), float(p[1])
        except (TypeError, ValueError, IndexError):
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        if out and abs(out[-1][0] - x) <= eps and abs(out[-1][1] - y) <= eps:
            continue
        out.append((x, y))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            if len(out) <= 3:
                break
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cross) <= eps * max(math.hypot(c[0] - a[0], c[1] - a[1]), 1e-9):
                out.pop(i)
                changed = True
                break
    return np.array(out, dtype=np.float64).reshape(-1, 2)


def triangulate(rings: list[np.ndarray]) -> np.ndarray:
    """Triangles (indices into the concatenated rings) of a polygon with holes, counter-clockwise."""
    verts = np.concatenate(rings).astype(np.float64)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    if _earcut is not None:
        tri = np.asarray(_earcut.triangulate_float64(verts, ends), dtype=np.int64).reshape(-1, 3)
    else:  # pragma: no cover - fan triangulation (no holes), good enough for convex outlines
        n = len(rings[0])
        tri = np.array([[0, i, i + 1] for i in range(1, n - 1)], dtype=np.int64)
    if len(tri):
        a, b, c = verts[tri[:, 0]], verts[tri[:, 1]], verts[tri[:, 2]]
        area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
        flip = area < 0
        tri[flip] = tri[flip][:, [0, 2, 1]]
    return tri


def round_segments(d: float) -> int:
    r = max(d / 2, 1e-4)
    e = min(0.002, r * 0.5)
    n = math.ceil(math.pi / math.acos(1 - e / r))
    return min(48, max(8, n + (n % 2)))


def circle(r: float, n: int, ccw: bool = True) -> np.ndarray:
    a = np.arange(n) / n * 2 * math.pi * (1 if ccw else -1)
    return np.stack([np.cos(a) * r, np.sin(a) * r], axis=1)


def rect(w: float, h: float) -> np.ndarray:
    return np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], dtype=np.float64)


def _centroid(ring: np.ndarray) -> np.ndarray:
    x, y = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    f = x * y1 - x1 * y
    a = f.sum()
    if abs(a) < 1e-12:
        return np.zeros(2)
    return np.array([((x + x1) * f).sum() / (3 * a), ((y + y1) * f).sum() / (3 * a)])


def profile_section(profile: Any) -> list[np.ndarray] | None:
    """Rings (outer counter-clockwise, holes clockwise) in (b, h) for a beam profile; None when it can't be drawn."""
    if not isinstance(profile, dict):
        return None
    P = lambda k: _num(profile.get(k), 0.0)  # noqa: E731
    shape = profile.get("shape")
    if shape == "rect":
        w, h = P("w"), P("h")
        return [rect(w, h)] if w > 0 and h > 0 else None
    if shape == "circle":
        d = P("d")
        return [circle(d / 2, round_segments(d))] if d > 0 else None
    if shape == "I":
        h, b = P("h"), P("b")
        tw, tf = min(P("tw"), b), min(P("tf"), h / 2)
        if not (h > 0 and b > 0 and tw > 0 and tf > 0):
            return None
        y0, y1 = -h / 2, h / 2
        return [np.array([[-b / 2, y0], [b / 2, y0], [b / 2, y0 + tf], [tw / 2, y0 + tf], [tw / 2, y1 - tf], [b / 2, y1 - tf],
                          [b / 2, y1], [-b / 2, y1], [-b / 2, y1 - tf], [-tw / 2, y1 - tf], [-tw / 2, y0 + tf], [-b / 2, y0 + tf]])]
    if shape == "C":
        h, b = P("h"), P("b")
        tw, tf = min(P("tw"), b), min(P("tf"), h / 2)
        if not (h > 0 and b > 0 and tw > 0 and tf > 0):
            return None
        ring = np.array([[-b / 2, -h / 2], [b / 2, -h / 2], [b / 2, -h / 2 + tf], [-b / 2 + tw, -h / 2 + tf],
                         [-b / 2 + tw, h / 2 - tf], [b / 2, h / 2 - tf], [b / 2, h / 2], [-b / 2, h / 2]])
        return [ring - _centroid(ring)]
    if shape == "L":
        h, b = P("h"), P("b")
        t = min(P("t"), b, h)
        if not (h > 0 and b > 0 and t > 0):
            return None
        ring = np.array([[-b / 2, -h / 2], [b / 2, -h / 2], [b / 2, -h / 2 + t], [-b / 2 + t, -h / 2 + t], [-b / 2 + t, h / 2], [-b / 2, h / 2]])
        return [ring - _centroid(ring)]
    if shape == "hss_rect":
        h, b, t = P("h"), P("b"), P("t")
        if not (h > 0 and b > 0 and t > 0):
            return None
        if 2 * t >= min(h, b) - 1e-6:
            return [rect(b, h)]
        return [rect(b, h), rect(b - 2 * t, h - 2 * t)[::-1]]
    if shape == "hss_round":
        d, t = P("d"), P("t")
        if not (d > 0 and t > 0):
            return None
        n = round_segments(d)
        if 2 * t >= d - 1e-6:
            return [circle(d / 2, n)]
        return [circle(d / 2, n), circle(d / 2 - t, n, ccw=False)]
    return None


def section_axes(u: np.ndarray, roll: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """The section's (b, h) axes for an axis u (packages/model members.ts sectionAxes)."""
    up = np.array([0.0, 1.0, 0.0]) if abs(u[2]) > math.cos(math.pi / 180) else np.array([0.0, 0.0, 1.0])
    h = up - u * np.dot(up, u)
    h /= np.linalg.norm(h)
    b = np.cross(h, u)
    if roll:
        c, s = math.cos(roll), math.sin(roll)
        b, h = b * c + h * s, h * c - b * s
    return b, h


def sweep(bld: Builder, rings: list[np.ndarray], start: np.ndarray, end: np.ndarray, b_axis: np.ndarray, h_axis: np.ndarray) -> None:
    """Extrude a section (rings in (b, h)) from start to end, with flat caps."""
    rings = [np.asarray(r, dtype=np.float64) for r in rings if len(r) >= 3]
    if not rings:
        return
    at = lambda o, pts: o + pts[:, :1] * b_axis + pts[:, 1:2] * h_axis  # noqa: E731
    tri = triangulate(rings)
    flat = np.concatenate(rings)
    if len(tri):
        bld.add(at(end, flat), tri)  # ccw in (b, h) faces +u
        bld.add(at(start, flat), tri[:, [0, 2, 1]])
    for ring in rings:
        s, e = at(start, ring), at(end, ring)
        n = len(ring)
        idx = np.arange(n)
        j = (idx + 1) % n
        v = np.concatenate([s, e])
        faces = np.concatenate([np.stack([idx, j, j + n], 1), np.stack([idx, j + n, idx + n], 1)])
        bld.add(v, faces)


def box_from(origin: np.ndarray, ax: np.ndarray, ay: np.ndarray, az: np.ndarray, lo: Iterable[float], hi: Iterable[float], bld: Builder) -> None:
    """An oriented box: corners origin + a·ax + b·ay + c·az over [lo, hi]."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    if x1 - x0 <= EPS or y1 - y0 <= EPS or z1 - z0 <= EPS:
        return
    P = lambda a, b, c: origin + a * ax + b * ay + c * az  # noqa: E731
    c = [P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)]
    faces = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    # keep outward winding whatever the axes' handedness
    if np.dot(np.cross(ax, ay), az) < 0:
        faces = faces[:, [0, 2, 1]]
    bld.add(np.array(c), faces)


class Model:
    """The model as the kernel sees it: elements by id (not deleted), levels' elevations, hosted children by host."""

    def __init__(self, read: dict):
        self.elements: dict[str, dict] = {}
        for e in list(read.get("levels") or []) + list(read.get("elements") or []):
            if e and not e.get("deleted"):
                self.elements[e["id"]] = e
        self.types = {t["id"]: t for t in read.get("types") or [] if not t.get("deleted")}
        self.seq = int(read.get("seq") or 0)
        self.children: dict[str, list[dict]] = {}
        self.walls_by_level: dict[str, list[dict]] = {}
        for e in self.elements.values():
            if e.get("parent_id") and e.get("kind") in HOSTED:
                self.children.setdefault(e["parent_id"], []).append(e)
            if e.get("kind") == "wall" and is_parametric(e):
                self.walls_by_level.setdefault(e.get("level_id") or "", []).append(e)

    @property
    def levels(self) -> list[dict]:
        return [e for e in self.elements.values() if e.get("kind") == "level"]

    def get(self, id: str | None) -> dict | None:
        return self.elements.get(id) if id else None

    def elevation(self, level_id: str | None) -> float:
        lvl = self.get(level_id)
        return _num(((lvl or {}).get("params") or {}).get("elevation"), 0.0)

    def vertical_extent(self, e: dict) -> tuple[float, float]:
        p = e.get("params") or {}
        base = self.elevation(e.get("level_id")) + _num(p.get("base_offset"), 0.0)
        top = p.get("top")
        z = base + 3
        if isinstance(top, dict) and isinstance(top.get("height"), (int, float)):
            z = base + float(top["height"])
        elif isinstance(top, dict) and top.get("level_id"):
            z = self.elevation(top["level_id"]) + _num(top.get("offset"), 0.0)
        elif isinstance(p.get("height"), (int, float)):
            z = base + float(p["height"])
        return base, z


def is_parametric(e: dict) -> bool:
    return ((e.get("geometry") or {}).get("mode") or "parametric") == "parametric"


@dataclass
class WallFrame:
    start: np.ndarray
    u: np.ndarray  # along, 2D
    v: np.ndarray  # left normal (side a), 2D
    length: float
    half: float
    base: float
    top: float

    def point(self, along: float, across: float, z: float) -> np.ndarray:
        p = self.start + self.u * along + self.v * across
        return np.array([p[0], p[1], z])

    @property
    def axes(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return np.array([self.u[0], self.u[1], 0.0]), np.array([self.v[0], self.v[1], 0.0]), np.array([0.0, 0.0, 1.0])

    @property
    def origin(self) -> np.ndarray:
        return np.array([self.start[0], self.start[1], 0.0])


def wall_frame(wall: dict, m: Model) -> WallFrame | None:
    p = wall.get("params") or {}
    s, e = p.get("start"), p.get("end")
    if not s or not e:
        return None
    s, e = np.array(s[:2], dtype=float), np.array(e[:2], dtype=float)
    d = e - s
    length = float(np.hypot(*d))
    if not length > 1e-6:
        return None
    u = d / length
    base, top = m.vertical_extent(wall)
    return WallFrame(s, u, np.array([-u[1], u[0]]), length, _num(p.get("thickness"), 0.1) / 2, base, top)


def hosted_rect(child: dict, f: WallFrame) -> tuple[float, float, float, float] | None:
    """(a0, a1, z0, z1) of the hole an opening/door/window cuts in its wall (packages/model hosting.ts)."""
    p = child.get("params") or {}
    wall_h = f.top - f.base
    width = min(_num(p.get("width"), 0.0), f.length)
    height = min(_num(p.get("height"), 0.0), wall_h)
    if not (width > 1e-4 and height > 1e-4):
        return None
    along = max(width / 2, min(f.length - width / 2, _num(p.get("along"), f.length / 2)))
    sill = max(0.0, min(wall_h - height, _num(p.get("sill"), 0.0)))
    return along - width / 2, along + width / 2, f.base + sill, f.base + sill + height


def _end_extension(wall: dict, f: WallFrame, at_start: bool, m: Model) -> float:
    """How far a wall end reaches into the wall it meets (that wall's half thickness), 0 when it meets none."""
    pt = f.start if at_start else f.start + f.u * f.length
    for other in m.walls_by_level.get(wall.get("level_id") or "", []):
        if other["id"] == wall["id"]:
            continue
        of = wall_frame(other, m)
        if not of:
            continue
        d = pt - of.start
        a = float(np.dot(d, of.u))
        c = abs(float(np.dot(d, of.v)))
        if -JOIN_TOL <= a <= of.length + JOIN_TOL and c <= JOIN_TOL:
            # not when the two run along each other
            if abs(float(np.dot(f.u, of.u))) < 0.99:
                return of.half
    return 0.0


def _subtract(lo: float, hi: float, cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out, at = [], lo
    for c0, c1 in sorted(c for c in cuts if c[1] > lo + EPS and c[0] < hi - EPS):
        if c0 > at + EPS:
            out.append((at, min(c0, hi)))
        at = max(at, c1)
        if at >= hi - EPS:
            break
    if at < hi - EPS:
        out.append((at, hi))
    return out


def wall_parts(wall: dict, m: Model) -> list[Part]:
    f = wall_frame(wall, m)
    if not f or not f.top - f.base > 1e-6:
        return []
    lo = -_end_extension(wall, f, True, m)
    hi = f.length + _end_extension(wall, f, False, m)
    holes = []
    for child in m.children.get(wall["id"], []):
        r = hosted_rect(child, f)
        if not r:
            continue
        a0, a1, z0, z1 = max(r[0], 0.0), min(r[1], f.length), max(r[2], f.base), min(r[3], f.top)
        if a1 - a0 > 1e-4 and z1 - z0 > 1e-4:
            holes.append((a0, a1, z0, z1))
    xs = sorted({lo, hi, *[x for h in holes for x in (h[0], h[1]) if lo < x < hi]})
    ax, ay, az = f.axes
    b = Builder()
    for x0, x1 in zip(xs, xs[1:]):
        if x1 - x0 <= EPS:
            continue
        mid = (x0 + x1) / 2
        cuts = [(h[2], h[3]) for h in holes if h[0] < mid < h[1]]
        for z0, z1 in _subtract(f.base, f.top, cuts):
            box_from(f.origin, ax, ay, az, (x0, -f.half, z0), (x1, f.half, z1), b)
    part = b.part("body", "wall")
    return [part] if part else []


def hosted_parts(child: dict, m: Model) -> list[Part]:
    if child.get("kind") == "opening":
        return []
    host = m.get(child.get("parent_id"))
    if not host or host.get("kind") != "wall":
        return []
    f = wall_frame(host, m)
    if not f:
        return []
    r = hosted_rect(child, f)
    if not r:
        return []
    a0, a1, z0, z1 = r
    W, H = a1 - a0, z1 - z0
    fw = min(FRAME, W / 4, H / 4)
    h = f.half
    ax, ay, az = f.axes
    o = f.origin
    box = lambda bld, x0, x1, w0, w1, zz0, zz1: box_from(o, ax, ay, az, (x0, w0, zz0), (x1, w1, zz1), bld)  # noqa: E731
    frame, parts = Builder(), []
    if child.get("kind") == "door":
        p = child.get("params") or {}
        box(frame, a0, a0 + fw, -h, h, z0, z1)
        box(frame, a1 - fw, a1, -h, h, z0, z1)
        box(frame, a0 + fw, a1 - fw, -h, h, z1 - fw, z1)
        leaf = Builder()
        t = min(0.045, h * 1.2)
        sign = -1 if p.get("opens") == "b" else 1
        inset = min(0.01, max(h - t, 0) / 2)
        wc = sign * max(h - t / 2 - inset, 0)
        gap = 0.004
        lo, hi = a0 + fw + gap, a1 - fw - gap
        lz0, lz1 = z0 + min(0.01, H / 20), z1 - fw - gap
        if p.get("leaves") == 2:
            mid = (lo + hi) / 2
            box(leaf, lo, mid - gap / 2, wc - t / 2, wc + t / 2, lz0, lz1)
            box(leaf, mid + gap / 2, hi, wc - t / 2, wc + t / 2, lz0, lz1)
        else:
            box(leaf, lo, hi, wc - t / 2, wc + t / 2, lz0, lz1)
        for bld, name in ((frame, "frame"), (leaf, "leaf")):
            part = bld.part(name, name)
            if part:
                parts.append(part)
        return parts
    d = min(h, 0.06)
    box(frame, a0, a0 + fw, -d, d, z0, z1)
    box(frame, a1 - fw, a1, -d, d, z0, z1)
    box(frame, a0 + fw, a1 - fw, -d, d, z1 - fw, z1)
    box(frame, a0 + fw, a1 - fw, -d, d, z0, z0 + fw)
    glass = Builder()
    g = min(0.006, d / 2)
    box(glass, a0 + fw, a1 - fw, -g, g, z0 + fw, z1 - fw)
    for bld, name in ((frame, "frame"), (glass, "glass")):
        part = bld.part(name, name)
        if part:
            parts.append(part)
    return parts


def slab_rings(p: dict) -> list[np.ndarray] | None:
    outer = clean_ring(p.get("outline") or [])
    if len(outer) < 3 or abs(ring_area(outer)) < 1e-8:
        return None
    if ring_area(outer) < 0:
        outer = outer[::-1]
    rings = [outer]
    for hole in p.get("holes") or []:
        r = clean_ring(hole)
        if len(r) < 3 or abs(ring_area(r)) < 1e-8:
            continue
        rings.append(r[::-1] if ring_area(r) > 0 else r)
    return rings


def slab_parts(slab: dict, m: Model) -> list[Part]:
    p = slab.get("params") or {}
    rings = slab_rings(p)
    thickness = _num(p.get("thickness"), 0.0)
    if not rings or not thickness > 0:
        return []
    top = m.elevation(slab.get("level_id")) + _num(p.get("offset"), 0.0)
    b = Builder()
    sweep(b, rings, np.array([0, 0, top - thickness]), np.array([0, 0, top]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
    role = p.get("role")
    part = b.part("body", "ceiling" if role == "ceiling" else "roof" if role == "roof" else "slab")
    return [part] if part else []


def _valid3(p: Any) -> bool:
    return isinstance(p, (list, tuple)) and len(p) == 3 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in p)


def member_part(start: Any, end: Any, rings: list[np.ndarray] | None, roll: float, name: str, material: str) -> Part | None:
    if not rings or not _valid3(start) or not _valid3(end):
        return None
    s, e = np.array(start, dtype=float), np.array(end, dtype=float)
    length = float(np.linalg.norm(e - s))
    if not length > 1e-6:
        return None
    u = (e - s) / length
    b_axis, h_axis = section_axes(u, roll)
    b = Builder()
    sweep(b, rings, s, e, b_axis, h_axis)
    return b.part(name, material)


def beam_parts(e: dict) -> list[Part]:
    p = e.get("params") or {}
    part = member_part(p.get("start"), p.get("end"), profile_section(p.get("profile")), _num(p.get("roll"), 0.0), "body", "beam")
    return [part] if part else []


def pipe_parts(e: dict) -> list[Part]:
    p = e.get("params") or {}
    od = _num(p.get("od"), 0.0)
    if not od > 0:
        return []
    parts = []
    body = member_part(p.get("start"), p.get("end"), [circle(od / 2, round_segments(od))], 0.0, "body", "pipe")
    if body:
        parts.append(body)
    ins_raw = p.get("insulation")
    ins = ins_raw if isinstance(ins_raw, (int, float)) else _num((ins_raw or {}).get("thickness") if isinstance(ins_raw, dict) else None, 0.0)
    if ins and ins > 0:
        d = od + 2 * ins
        jacket = member_part(p.get("start"), p.get("end"), [circle(d / 2, round_segments(d))], 0.0, "insulation", "insulation")
        if jacket:
            parts.append(jacket)
    return parts


def duct_section(p: dict) -> list[np.ndarray] | None:
    s = p.get("section") or {}
    if s.get("shape") == "round" and _num(s.get("d"), 0) > 0:
        return [circle(s["d"] / 2, round_segments(s["d"]))]
    if s.get("shape") == "rect" and _num(s.get("w"), 0) > 0 and _num(s.get("h"), 0) > 0:
        return [rect(s["w"], s["h"])]
    return None


def duct_parts(e: dict) -> list[Part]:
    p = e.get("params") or {}
    part = member_part(p.get("start"), p.get("end"), duct_section(p), _num(p.get("roll"), 0.0), "body", "duct")
    return [part] if part else []


def column_section(p: dict) -> list[np.ndarray] | None:
    s = p.get("section") or {}
    if s.get("shape") == "rect" and _num(s.get("w"), 0) > 0 and _num(s.get("d"), 0) > 0:
        return [rect(s["w"], s["d"])]
    if s.get("shape") == "circle" and _num(s.get("d"), 0) > 0:
        return [circle(s["d"] / 2, round_segments(s["d"]))]
    return None


def column_parts(e: dict, m: Model) -> list[Part]:
    p = e.get("params") or {}
    pos = p.get("position")
    if not pos or len(pos) < 2:
        return []
    base, top = m.vertical_extent(e)
    if not top - base > 1e-6:
        return []
    rings = column_section(p)
    if not rings:
        return []
    r = _num(p.get("rotation"), 0.0)
    w_axis = np.array([math.cos(r), math.sin(r), 0.0])
    d_axis = np.array([-math.sin(r), math.cos(r), 0.0])
    b = Builder()
    sweep(b, rings, np.array([pos[0], pos[1], base]), np.array([pos[0], pos[1], top]), w_axis, d_axis)
    part = b.part("body", "column")
    return [part] if part else []


def quat_matrix(q: Iterable[float]) -> np.ndarray:
    x, y, z, w = (float(v) for v in q)
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


# glTF (+Y up) → working frame (+Z up): (x, y, z)work = (x, −z, y)gltf
GLTF_TO_WORK = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])


MeshLoader = Callable[[str], "list[tuple[str, np.ndarray, np.ndarray]]"]
"""sha → [(part name, vertices in the mesh's own glTF frame, faces)]"""


def mesh_parts(e: dict, load: MeshLoader | None) -> list[Part]:
    g = e.get("geometry") or {}
    sha = (g.get("mesh") or {}).get("sha")
    if not sha or load is None:
        return []
    t = np.array(g.get("t") or [0, 0, 0], dtype=float)
    R = quat_matrix(g.get("q") or [0, 0, 0, 1])
    out = []
    for name, v, f in load(sha):
        world = (np.asarray(v, dtype=float) @ GLTF_TO_WORK.T) @ R.T + t
        out.append(Part(name or "body", "mesh", world, np.asarray(f, dtype=np.int64)))
    return out


def element_parts(e: dict, m: Model, load_mesh: MeshLoader | None = None) -> list[Part]:
    """What an element draws. Never raises: an element it can't draw comes back with no parts."""
    try:
        if not is_parametric(e):
            return mesh_parts(e, load_mesh)
        kind = e.get("kind")
        if kind == "wall":
            return wall_parts(e, m)
        if kind == "slab":
            return slab_parts(e, m)
        if kind in HOSTED:
            return hosted_parts(e, m)
        if kind == "column":
            return column_parts(e, m)
        if kind == "beam":
            return beam_parts(e)
        if kind == "pipe":
            return pipe_parts(e)
        if kind == "duct":
            return duct_parts(e)
    except Exception:  # noqa: BLE001 - one bad element must not stop a build
        return []
    return []


def all_parts(m: Model, load_mesh: MeshLoader | None = None) -> dict[str, list[Part]]:
    return {id: parts for id, e in m.elements.items() if e.get("kind") != "level" and (parts := element_parts(e, m, load_mesh))}


def ifc_class_of(e: dict) -> str:
    return e.get("ifc_class") or IFC_CLASS.get(e.get("kind") or "", "IfcBuildingElementProxy")
