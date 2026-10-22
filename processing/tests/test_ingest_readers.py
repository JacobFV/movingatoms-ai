"""Every reader on a tiny synthetic file: the points, colours and intensities come back as written."""
from __future__ import annotations

import struct
import zipfile
from pathlib import Path

import laspy
import numpy as np
import pytest

from ma_proc.ingest import readers

RNG = np.random.default_rng(1)
N = 500
XYZ = np.round(RNG.random((N, 3)) * [5, 4, 3], 3)
RGB8 = RNG.integers(0, 256, (N, 3)).astype(np.uint8)
INT = RNG.integers(0, 65536, N).astype(np.uint16)


def collect(path: Path):
    chunks = list(readers.read(path))
    xyz = np.concatenate([c["xyz"] for c in chunks])
    rgb = None if chunks[0]["rgb"] is None else np.concatenate([c["rgb"] for c in chunks])
    it = None if chunks[0]["intensity"] is None else np.concatenate([c["intensity"] for c in chunks])
    return xyz, rgb, it


def test_las_and_laz(tmp_path: Path):
    for ext in ("las", "laz"):
        h = laspy.LasHeader(point_format=7, version="1.4")
        h.scales = [0.001] * 3
        h.offsets = [0, 0, 0]
        las = laspy.LasData(h)
        las.x, las.y, las.z = XYZ[:, 0], XYZ[:, 1], XYZ[:, 2]
        las.red, las.green, las.blue = (RGB8.astype(np.uint16) * 257).T
        las.intensity = INT
        p = tmp_path / f"t.{ext}"
        las.write(p)
        xyz, rgb, it = collect(p)
        assert np.allclose(xyz, XYZ, atol=1e-3)
        assert np.array_equal(rgb >> 8, RGB8)
        assert np.array_equal(it, INT)


def test_ply_binary_and_ascii(tmp_path: Path):
    from plyfile import PlyData, PlyElement

    v = np.zeros(N, dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("red", "u1"), ("green", "u1"), ("blue", "u1")])
    v["x"], v["y"], v["z"] = XYZ.T
    v["red"], v["green"], v["blue"] = RGB8.T
    for text in (False, True):
        p = tmp_path / f"t{int(text)}.ply"
        PlyData([PlyElement.describe(v, "vertex")], text=text).write(str(p))
        xyz, rgb, _ = collect(p)
        assert np.allclose(xyz, XYZ, atol=1e-3)
        assert np.array_equal((rgb // 257).astype(np.uint8), RGB8)


def test_gaussian_splat_ply(tmp_path: Path):
    from plyfile import PlyData, PlyElement

    v = np.zeros(N, dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("f_dc_0", "f4"), ("f_dc_1", "f4"), ("f_dc_2", "f4"), ("opacity", "f4")])
    v["x"], v["y"], v["z"] = XYZ.T
    v["f_dc_0"] = 1.0  # 0.5 + 0.282 → bright red channel
    p = tmp_path / "splat.ply"
    PlyData([PlyElement.describe(v, "vertex")]).write(str(p))
    _, rgb, _ = collect(p)
    assert rgb[:, 0].min() > rgb[:, 1].max()


def test_text_formats(tmp_path: Path):
    rows = [f"{x} {y} {z} {i} {r} {g} {b}" for (x, y, z), i, (r, g, b) in zip(XYZ, INT, RGB8)]
    (tmp_path / "t.pts").write_text(f"{N}\n" + "\n".join(rows))
    xyz, rgb, it = collect(tmp_path / "t.pts")
    assert np.allclose(xyz, XYZ) and rgb is not None and it is not None
    (tmp_path / "t.xyz").write_text("\n".join(f"{x} {y} {z}" for x, y, z in XYZ))
    xyz, rgb, it = collect(tmp_path / "t.xyz")
    assert np.allclose(xyz, XYZ) and rgb is None and it is None
    (tmp_path / "t.csv").write_text("x,y,z,r,g,b\n" + "\n".join(f"{x},{y},{z},{r},{g},{b}" for (x, y, z), (r, g, b) in zip(XYZ, RGB8)))
    xyz, rgb, _ = collect(tmp_path / "t.csv")
    assert np.allclose(xyz, XYZ) and np.array_equal((rgb // 257).astype(np.uint8), RGB8)


def test_ptx(tmp_path: Path):
    cols, rows = 25, 20
    head = [str(cols), str(rows), "0 0 0", "1 0 0", "0 1 0", "0 0 1", "1 0 0 0", "0 1 0 0", "0 0 1 0", "10 20 30 1"]
    body = [f"{x} {y} {z} 0.5 {r} {g} {b}" for (x, y, z), (r, g, b) in zip(XYZ, RGB8)]
    body[0] = "0 0 0 0.5 0 0 0"  # a no-return
    (tmp_path / "t.ptx").write_text("\n".join(head + body) + "\n")
    xyz, rgb, it = collect(tmp_path / "t.ptx")
    assert len(xyz) == N - 1
    assert np.allclose(xyz, XYZ[1:] + [10, 20, 30])  # the setup's transform applied
    assert readers.positions(tmp_path / "t.ptx") == 1


def test_pcd_binary(tmp_path: Path):
    packed = (RGB8[:, 0].astype(np.uint32) << 16) | (RGB8[:, 1].astype(np.uint32) << 8) | RGB8[:, 2]
    head = f"VERSION .7\nFIELDS x y z rgb\nSIZE 4 4 4 4\nTYPE F F F F\nCOUNT 1 1 1 1\nWIDTH {N}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {N}\nDATA binary\n"
    data = np.zeros(N, dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("rgb", "f4")])
    data["x"], data["y"], data["z"] = XYZ.T
    data["rgb"] = packed.view(np.float32)
    (tmp_path / "t.pcd").write_bytes(head.encode() + data.tobytes())
    xyz, rgb, _ = collect(tmp_path / "t.pcd")
    assert np.allclose(xyz, XYZ, atol=1e-3)
    assert np.array_equal((rgb // 257).astype(np.uint8), RGB8)


def test_e57(tmp_path: Path):
    pye57 = pytest.importorskip("pye57")
    p = tmp_path / "t.e57"
    e = pye57.E57(str(p), mode="w")
    e.write_scan_raw({"cartesianX": XYZ[:, 0], "cartesianY": XYZ[:, 1], "cartesianZ": XYZ[:, 2],
                      "colorRed": RGB8[:, 0], "colorGreen": RGB8[:, 1], "colorBlue": RGB8[:, 2]})
    e.close()
    xyz, rgb, _ = collect(p)
    assert np.allclose(np.sort(xyz, axis=0), np.sort(XYZ, axis=0), atol=1e-3)
    assert rgb is not None
    assert readers.positions(p) == 1


def test_mesh_is_sampled(tmp_path: Path):
    import trimesh

    trimesh.creation.box(extents=[2, 3, 1]).export(tmp_path / "box.stl")
    xyz, _, _ = collect(tmp_path / "box.stl")
    assert len(xyz) > 1000
    assert np.allclose(xyz.min(axis=0), [-1, -1.5, -0.5], atol=1e-6)


def test_zip_and_recap(tmp_path: Path):
    (tmp_path / "a.xyz").write_text("\n".join(f"{x} {y} {z}" for x, y, z in XYZ))
    with zipfile.ZipFile(tmp_path / "s.zip", "w") as z:
        z.write(tmp_path / "a.xyz", "scan/a.xyz")
        z.writestr("readme.txt.md", "not a scan")
    out = readers.unzip_points(tmp_path / "s.zip", tmp_path / "x")
    assert [p.name for p in out] == ["a.xyz"]
    with pytest.raises(readers.Unreadable, match="Export the scan as E57"):
        readers.read(tmp_path / "project.rcp")
    with pytest.raises(readers.Unreadable):
        readers.kind(tmp_path / "doc.docx")
