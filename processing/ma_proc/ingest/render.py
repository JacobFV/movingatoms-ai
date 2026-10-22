"""Overview pictures of a scan: a top view and a north-east isometric view, splatted from the points with a depth
buffer (numpy only), coloured by the scan's own colours or by its labels."""
from __future__ import annotations

import numpy as np
from PIL import Image

# ma-v1 colours (types.ts LABELS)
LABEL_RGB = {0: "#8a949a", 1: "#c8b78a", 2: "#9fb0c4", 3: "#e6e1d3", 4: "#f08a4b", 5: "#e05a4f", 6: "#3fa7f5", 7: "#76d4c6",
             8: "#9bd158", 9: "#c48af7", 10: "#f2a6c4", 11: "#b48a63", 12: "#5fb86e", 18: "#535b61"}
_LUT = np.zeros((256, 3), np.uint8)
for k, h in LABEL_RGB.items():
    _LUT[k] = [int(h[i : i + 2], 16) for i in (1, 3, 5)]

BG = np.array([10, 10, 10], np.uint8)


def label_colors(lab: np.ndarray) -> np.ndarray:
    return _LUT[lab]


def _view(xyz: np.ndarray, view: str) -> tuple[np.ndarray, np.ndarray]:
    """Screen x, y (up) and depth (larger = nearer) for a view."""
    c = xyz - xyz.mean(axis=0)
    if view == "top":
        return c[:, :2], c[:, 2]
    if view in ("iso_ne", "iso_sw"):
        # looking from the north-east (or south-west), 35° down
        az, el = np.radians(225.0 if view == "iso_ne" else 45.0), np.radians(35.0)
        fwd = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), -np.sin(el)])
        up = np.array([0.0, 0.0, 1.0]) - (fwd @ [0.0, 0.0, 1.0]) * fwd
        up /= np.linalg.norm(up)
        right = np.cross(fwd, up)
        return np.column_stack([c @ right, c @ up]), -(c @ fwd)
    if view in ("front", "side_y"):
        # looking north (along +y): x across, z up
        return c[:, [0, 2]], -c[:, 1]
    if view == "side_x":
        # looking west (along -x): y across, z up
        return c[:, [1, 2]], c[:, 0]
    raise ValueError(view)


def render(xyz: np.ndarray, rgb: np.ndarray, view: str = "top", width: int = 1600, max_h: int = 1200,
           shade: bool = True, cut_ceiling: float | None = None, stretch: bool = True) -> Image.Image:
    """`rgb` uint8 (N,3). `cut_ceiling`: hide points above this height (a top view sees the room, not its roof)."""
    if cut_ceiling is not None:
        keep = xyz[:, 2] < cut_ceiling
        xyz, rgb = xyz[keep], rgb[keep]
    if len(xyz) == 0:
        return Image.new("RGB", (width, max_h // 2), tuple(BG))
    s, depth = _view(xyz, view)
    lo, hi = np.percentile(s, 0.02, axis=0), np.percentile(s, 99.98, axis=0)
    span = np.maximum(hi - lo, 1e-6)
    scale = min((width - 40) / span[0], (max_h - 40) / span[1])
    w = int(span[0] * scale) + 40
    h = int(span[1] * scale) + 40
    px = ((s[:, 0] - lo[0]) * scale + 20).astype(np.int64)
    py = (h - 1 - ((s[:, 1] - lo[1]) * scale + 20)).astype(np.int64)
    ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
    px, py, depth, rgb = px[ok], py[ok], depth[ok], rgb[ok]
    # splat size from point density: fill the gaps between points
    density = len(px) / max(1.0, float(w * h))
    rad = 0 if density > 1.5 else 1 if density > 0.3 else 2
    order = np.argsort(depth)  # far first: nearer points overwrite
    px, py, depth, rgb = px[order], py[order], depth[order], rgb[order]
    img = np.empty((h, w, 3), np.uint8)
    img[:] = BG
    col = rgb.astype(np.float32)
    # stretch the colours (scanner colours are often dark)
    lo_c, hi_c = np.percentile(col, 1), np.percentile(col, 99)
    if stretch and hi_c - lo_c > 10:
        col = (col - lo_c) * (235.0 / (hi_c - lo_c)) + 10
    if shade:
        d = (depth - depth.min()) / max(1e-6, float(np.ptp(depth)))
        col = col * (0.7 + 0.3 * d[:, None])
    col = np.clip(col, 0, 255).astype(np.uint8)
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            x = np.clip(px + dx, 0, w - 1)
            y = np.clip(py + dy, 0, h - 1)
            img[y, x] = col
    out = Image.fromarray(img)
    if view in ("top", "front", "side_x", "side_y"):
        _annotate(out, scale, north=view == "top")
    return out


def _annotate(img: Image.Image, px_per_m: float, north: bool) -> None:
    """A scale bar (a round length, about a fifth of the width) and, on plans, a north arrow."""
    from PIL import ImageDraw

    d = ImageDraw.Draw(img)
    w, h = img.size
    target = w / 5 / px_per_m
    nice = min((x for x in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if x >= target * 0.6), default=1000)
    bar = int(nice * px_per_m)
    x0, y0 = 24, h - 26
    d.rectangle([x0, y0, x0 + bar, y0 + 5], fill=(235, 235, 235))
    label = f"{nice:g} m" if nice >= 1 else f"{int(nice * 1000)} mm"
    d.text((x0, y0 - 16), label, fill=(235, 235, 235))
    if north:
        cx, cy = w - 36, 30
        d.polygon([(cx, cy - 14), (cx - 9, cy + 12), (cx, cy + 6), (cx + 9, cy + 12)], fill=(235, 235, 235))
        d.text((cx - 4, cy + 15), "N", fill=(235, 235, 235))
