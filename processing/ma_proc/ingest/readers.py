"""Point readers: every supported format yields chunks of points, so a scan of any size streams through bounded memory.

A chunk is a dict: xyz (N,3) float64 in the file's own frame, rgb (N,3) uint16 0..65535 or None, intensity (N,) uint16
or None. `positions(path)` says how many scan positions (setups) the file holds, for progress text.
"""
from __future__ import annotations

import io
import os
import struct
import zipfile
from pathlib import Path
from typing import Iterator

import numpy as np

CHUNK = 2_000_000

POINT_EXTS = {".las", ".laz", ".e57", ".ply", ".pts", ".ptx", ".xyz", ".txt", ".csv", ".pcd"}
MESH_EXTS = {".glb", ".gltf", ".obj", ".stl", ".fbx", ".dae", ".3ds", ".x3d", ".3mf"}
RECAP_EXTS = {".rcp", ".rcs"}


class Unreadable(ValueError):
    """A file we can't read, with a message the customer can act on."""


class TooBig(RuntimeError):
    """The scan is bigger than this worker takes (MA_MAX_SOURCE_BYTES): the job goes back for a bigger machine."""


Chunk = dict


def _u16(a: np.ndarray, maxv: float | None = None) -> np.ndarray:
    """Colours or intensities to uint16 (0..65535), whatever range they came in."""
    a = np.asarray(a)
    if a.size == 0:
        return a.astype(np.uint16)
    if maxv is None:
        m = float(np.nanmax(a)) if a.size else 0.0
        maxv = 1.0 if m <= 1.0 else 255.0 if m <= 255 else 65535.0
    return np.clip(np.nan_to_num(a.astype(np.float64)) / maxv * 65535.0, 0, 65535).astype(np.uint16)


# ---------------------------------------------------------------- LAS / LAZ

def _las(path: Path) -> Iterator[Chunk]:
    import laspy

    with laspy.open(path) as f:
        dims = set(f.header.point_format.dimension_names)
        has_rgb = {"red", "green", "blue"} <= dims
        for pts in f.chunk_iterator(CHUNK):
            xyz = np.column_stack([np.asarray(pts.x), np.asarray(pts.y), np.asarray(pts.z)])
            rgb = None
            if has_rgb:
                rgb = np.column_stack([np.asarray(pts.red), np.asarray(pts.green), np.asarray(pts.blue)]).astype(np.uint16)
                if rgb.size and rgb.max() <= 255:  # 8-bit colours stored in 16-bit fields
                    rgb = (rgb.astype(np.uint32) * 257).astype(np.uint16)
            inten = np.asarray(pts.intensity).astype(np.uint16) if "intensity" in dims else None
            yield {"xyz": xyz, "rgb": rgb, "intensity": inten}


def _las_crs(path: Path) -> str | None:
    try:
        import laspy

        with laspy.open(path) as f:
            crs = f.header.parse_crs()
            return crs.to_string() if crs else None
    except Exception:
        return None


# ---------------------------------------------------------------- E57

def _e57(path: Path) -> Iterator[Chunk]:
    """Every scan position, read in fixed-size chunks through libE57's compressed-vector reader (pye57's read_scan
    would load a whole position into memory), each placed in the project by its pose."""
    import pye57
    from pye57 import libe57

    e = pye57.E57(str(path))
    for i in range(e.scan_count):
        h = e.get_header(i)
        fields = set(h.point_fields)
        cart = {"cartesianX", "cartesianY", "cartesianZ"} <= fields
        sph = {"sphericalRange", "sphericalAzimuth", "sphericalElevation"} <= fields
        if not (cart or sph):
            continue
        want = (["cartesianX", "cartesianY", "cartesianZ"] if cart else ["sphericalRange", "sphericalAzimuth", "sphericalElevation"])
        want += [f for f in ("cartesianInvalidState" if cart else "sphericalInvalidState", "intensity", "colorRed", "colorGreen", "colorBlue") if f in fields]
        cap = min(CHUNK, max(1, int(h.point_count)))
        data, buffers = e.make_buffers(want, cap)
        reader = h.points.reader(buffers)
        rot, trans = h.rotation_matrix, h.translation
        cmax = _e57_limits(h, "colorRedLimits")
        imax = _e57_limits(h, "intensityLimits")
        try:
            while True:
                n = reader.read()
                if n == 0:
                    break
                if cart:
                    p = np.column_stack([data["cartesianX"][:n], data["cartesianY"][:n], data["cartesianZ"][:n]]).astype(np.float64)
                else:
                    r, az, el = data["sphericalRange"][:n], data["sphericalAzimuth"][:n], data["sphericalElevation"][:n]
                    p = np.column_stack([r * np.cos(el) * np.cos(az), r * np.cos(el) * np.sin(az), r * np.sin(el)]).astype(np.float64)
                keep = np.ones(n, bool)
                inv = "cartesianInvalidState" if cart else "sphericalInvalidState"
                if inv in data:
                    keep = data[inv][:n] == 0
                p = p[keep] @ rot.T + trans
                rgb = None
                if "colorRed" in data:
                    rgb = _u16(np.column_stack([data["colorRed"][:n], data["colorGreen"][:n], data["colorBlue"][:n]])[keep], cmax)
                inten = _u16(data["intensity"][:n][keep], imax) if "intensity" in data else None
                yield {"xyz": p, "rgb": rgb, "intensity": inten}
        finally:
            reader.close()


def _e57_limits(h, name: str) -> float | None:
    """The maximum of a colour/intensity limits node, so values scale the way the scanner meant."""
    try:
        node = h.node[name]
        key = "colorRedMaximum" if name.startswith("color") else "intensityMaximum"
        return float(node[key].value())
    except Exception:
        return None


def _e57_positions(path: Path) -> int:
    import pye57

    return pye57.E57(str(path)).scan_count


# ---------------------------------------------------------------- PLY (ascii and binary, incl. Gaussian splats)

SH_C0 = 0.28209479177387814


def _ply(path: Path) -> Iterator[Chunk]:
    from plyfile import PlyData

    ply = PlyData.read(str(path), mmap=True)
    if "vertex" not in ply:
        raise Unreadable("This PLY file has no points.")
    v = ply["vertex"]
    names = set(v.data.dtype.names or ())
    n = v.count
    faces = "face" in ply and ply["face"].count > 0
    if faces and n < 5_000_000:
        # a mesh: sample its surface instead of using only the vertices
        yield from _mesh(path)
        return
    for s in range(0, n, CHUNK):
        d = v.data[s : s + CHUNK]
        xyz = np.column_stack([d["x"], d["y"], d["z"]]).astype(np.float64)
        rgb = None
        if {"red", "green", "blue"} <= names:
            rgb = _u16(np.column_stack([d["red"], d["green"], d["blue"]]), 255.0 if d["red"].dtype == np.uint8 else None)
        elif {"r", "g", "b"} <= names:
            rgb = _u16(np.column_stack([d["r"], d["g"], d["b"]]))
        elif {"f_dc_0", "f_dc_1", "f_dc_2"} <= names:  # 3D Gaussian splats: the zero-order spherical harmonic is the colour
            c = 0.5 + SH_C0 * np.column_stack([d["f_dc_0"], d["f_dc_1"], d["f_dc_2"]]).astype(np.float64)
            rgb = _u16(np.clip(c, 0, 1), 1.0)
        inten = None
        for k in ("intensity", "scalar_intensity", "scalar_Intensity", "reflectance"):
            if k in names:
                inten = _u16(d[k])
                break
        yield {"xyz": xyz, "rgb": rgb, "intensity": inten}


# ---------------------------------------------------------------- text formats: PTS, XYZ, TXT, CSV, PTX

def _text_columns(first: list[str]) -> tuple[int, bool, bool]:
    """(columns, has_intensity, has_rgb) from the first data row."""
    c = len(first)
    if c >= 7:
        return c, True, True  # x y z i r g b
    if c == 6:
        return c, False, True  # x y z r g b
    if c == 4:
        return c, True, False  # x y z i
    return c, False, False


def _text(path: Path) -> Iterator[Chunk]:
    delim = "," if path.suffix.lower() == ".csv" else None
    with open(path, "r", errors="replace") as f:
        lines: list[str] = []
        cols = None
        for line in f:
            t = line.strip()
            if not t or t[0] in "#/":
                continue
            parts = t.replace(",", " ").split() if delim else t.split()
            if cols is None:
                try:
                    [float(p) for p in parts]
                except ValueError:
                    continue  # a header row
                if len(parts) == 1:
                    continue  # the PTS point count line
                cols = _text_columns(parts)
            if len(parts) != cols[0]:
                continue
            lines.append(" ".join(parts))
            if len(lines) >= CHUNK:
                yield _text_chunk(lines, cols)
                lines = []
        if lines and cols:
            yield _text_chunk(lines, cols)
        if cols is None:
            raise Unreadable("We couldn't find any points in this text file. It needs one point per line: x y z (and optionally intensity and r g b).")


def _text_chunk(lines: list[str], cols: tuple[int, bool, bool]) -> Chunk:
    a = np.loadtxt(io.StringIO("\n".join(lines)), dtype=np.float64, ndmin=2)
    n, has_i, has_rgb = cols
    xyz = a[:, :3]
    inten = _u16(a[:, 3]) if has_i else None
    rgb = None
    if has_rgb:
        rgb = _u16(a[:, n - 3 : n], 255.0 if a[:, n - 3 : n].max() > 1 else 1.0)
    return {"xyz": xyz, "rgb": rgb, "intensity": inten}


def _ptx(path: Path) -> Iterator[Chunk]:
    """Leica PTX: per setup a header (cols, rows, scanner position + axes, 4x4 transform) then rows*cols points."""
    with open(path, "r", errors="replace") as f:
        while True:
            head = [f.readline() for _ in range(10)]
            if not head[0].strip():
                return
            cols, rows = int(head[0]), int(head[1])
            m = np.array([[float(x) for x in head[6 + i].split()] for i in range(4)])
            buf: list[str] = []
            remaining = cols * rows
            while remaining > 0:
                take = min(remaining, CHUNK)
                buf = [f.readline() for _ in range(take)]
                remaining -= take
                a = np.loadtxt(io.StringIO("".join(buf)), dtype=np.float64, ndmin=2)
                keep = np.any(a[:, :3] != 0, axis=1)  # zero rows are no-returns
                a = a[keep]
                if not len(a):
                    continue
                xyz = a[:, :3] @ m[:3, :3] + m[3, :3]
                inten = _u16(a[:, 3], 1.0) if a.shape[1] >= 4 else None
                rgb = _u16(a[:, 4:7], 255.0) if a.shape[1] >= 7 else None
                yield {"xyz": xyz, "rgb": rgb, "intensity": inten}


def _ptx_positions(path: Path) -> int:
    n = 0
    with open(path, "r", errors="replace") as f:
        while True:
            a = f.readline()
            if not a.strip():
                return max(1, n)
            b = f.readline()
            cols, rows = int(a), int(b)
            for _ in range(8 + cols * rows):
                f.readline()
            n += 1


# ---------------------------------------------------------------- PCD

_PCD_TYPES = {("F", 4): "f4", ("F", 8): "f8", ("U", 1): "u1", ("U", 2): "u2", ("U", 4): "u4", ("I", 1): "i1", ("I", 2): "i2", ("I", 4): "i4"}


def _pcd(path: Path) -> Iterator[Chunk]:
    with open(path, "rb") as f:
        header: dict[str, list[str]] = {}
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if not line or line.startswith("#"):
                continue
            k, *v = line.split()
            header[k.upper()] = v
            if k.upper() == "DATA":
                break
        fields, sizes, types = header["FIELDS"], [int(s) for s in header["SIZE"]], header["TYPE"]
        counts = [int(c) for c in header.get("COUNT", ["1"] * len(fields))]
        n = int(header["POINTS"][0])
        dtype = np.dtype([(fi if c == 1 else f"{fi}_{j}", _PCD_TYPES[(t, s)]) for fi, s, t, c in zip(fields, sizes, types, counts) for j in range(c)])
        mode = header["DATA"][0].lower()
        if mode == "binary":
            data = np.frombuffer(f.read(n * dtype.itemsize), dtype=dtype, count=n)
        elif mode == "ascii":
            data = np.loadtxt(f, dtype=dtype, ndmin=1)
        else:
            raise Unreadable("Compressed PCD files aren't supported. Save it as binary or ASCII PCD, or as PLY/LAS.")
    names = set(data.dtype.names)
    for s in range(0, len(data), CHUNK):
        d = data[s : s + CHUNK]
        xyz = np.column_stack([d["x"], d["y"], d["z"]]).astype(np.float64)
        ok = np.isfinite(xyz).all(axis=1)
        rgb = None
        if "rgb" in names or "rgba" in names:
            packed = d["rgb" if "rgb" in names else "rgba"]
            u = packed.view(np.uint32) if packed.dtype.kind == "f" else packed.astype(np.uint32)
            rgb = _u16(np.column_stack([(u >> 16) & 255, (u >> 8) & 255, u & 255]), 255.0)
        inten = _u16(d["intensity"]) if "intensity" in names else None
        yield {"xyz": xyz[ok], "rgb": None if rgb is None else rgb[ok], "intensity": None if inten is None else inten[ok]}


# ---------------------------------------------------------------- meshes: sample the surface

def _mesh(path: Path, points: int = 4_000_000) -> Iterator[Chunk]:
    import trimesh

    loaded = trimesh.load(str(path), force="scene")
    meshes = [g for g in loaded.dump() if isinstance(g, trimesh.Trimesh) and len(g.faces)] if isinstance(loaded, trimesh.Scene) else [loaded]
    if not meshes:
        raise Unreadable("This model has no surfaces we can sample.")
    area = sum(m.area for m in meshes) or 1.0
    for m in meshes:
        k = max(100, int(points * m.area / area))
        pts, face = trimesh.sample.sample_surface(m, k)
        rgb = None
        try:
            vc = m.visual.to_color().face_colors if hasattr(m.visual, "to_color") else None
            if vc is not None and len(vc) == len(m.faces):
                rgb = _u16(vc[face, :3], 255.0)
        except Exception:
            rgb = None
        yield {"xyz": np.asarray(pts, dtype=np.float64), "rgb": rgb, "intensity": None}


# ---------------------------------------------------------------- ZIP: the point files inside

def unzip_points(path: Path, dest: Path) -> list[Path]:
    """Extract the readable point (or mesh) files in a zip; NavVis and other exports pack E57/LAS/PLY this way."""
    out: list[Path] = []
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as z:
        members = [m for m in z.infolist() if not m.is_dir() and not os.path.basename(m.filename).startswith(".")]
        names = [m for m in members if Path(m.filename).suffix.lower() in POINT_EXTS]
        if not names:
            names = [m for m in members if Path(m.filename).suffix.lower() in MESH_EXTS]
        for m in names:
            if ".." in Path(m.filename).parts:
                continue
            target = dest / Path(m.filename).name
            with z.open(m) as src, open(target, "wb") as dst:
                while b := src.read(16 * 1024 * 1024):
                    dst.write(b)
            out.append(target)
    if not out:
        raise Unreadable("This zip has no point clouds we can read (E57, LAS/LAZ, PLY, PTS, PTX, XYZ) inside.")
    return out


# ---------------------------------------------------------------- dispatch

def kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in RECAP_EXTS:
        return "recap"
    if ext == ".zip":
        return "zip"
    if ext in MESH_EXTS:
        return "mesh"
    if ext in POINT_EXTS:
        return ext[1:]
    raise Unreadable(f"We can't read {ext or 'this kind of'} files. Send the scan as E57, LAS/LAZ, PLY, PTS, PTX or XYZ.")


def read(path: Path) -> Iterator[Chunk]:
    k = kind(path)
    if k == "recap":
        raise Unreadable("ReCap projects can't be read directly. Export the scan as E57 from ReCap and upload that.")
    if k in ("las", "laz"):
        return _las(path)
    if k == "e57":
        return _e57(path)
    if k == "ply":
        return _ply(path)
    if k == "ptx":
        return _ptx(path)
    if k == "pcd":
        return _pcd(path)
    if k in ("pts", "xyz", "txt", "csv"):
        return _text(path)
    if k == "mesh":
        return _mesh(path)
    raise Unreadable(f"Unsupported file: {path.name}")


def positions(path: Path) -> int:
    k = kind(path)
    try:
        if k == "e57":
            return _e57_positions(path)
        if k == "ptx":
            return _ptx_positions(path)
    except Exception:
        pass
    return 1


def crs(path: Path) -> str | None:
    return _las_crs(path) if kind(path) in ("las", "laz") else None
