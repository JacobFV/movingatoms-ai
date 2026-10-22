"""ma_proc.model on a synthetic room: geometry, build files (GLB + IFC), fit to scan and heatmaps.
Run: uv run --with numpy --with scipy --with trimesh --with mapbox-earcut --with ifcopenshell --with laspy --with requests --with pytest pytest processing/tests"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ma_proc.model import fit as fitmod  # noqa: E402
from ma_proc.model import heatmap as heat  # noqa: E402
from ma_proc.model.build import build_files  # noqa: E402
from ma_proc.model.geometry import Model, all_parts, element_parts, wall_frame  # noqa: E402
from ma_proc.model.points import decode_octree  # noqa: E402


def room() -> dict:
    lvl = {"id": "lvl_ground0000000000", "kind": "level", "params": {"elevation": 0}, "props": {"name": "Ground"}, "version": 1}
    walls = []
    corners = [(0, 0), (6, 0), (6, 4), (0, 4)]
    for i in range(4):
        s, e = corners[i], corners[(i + 1) % 4]
        walls.append({"id": f"wall_{i:016d}", "kind": "wall", "level_id": lvl["id"], "params": {"start": list(s), "end": list(e), "thickness": 0.2, "height": 3},
                      "props": {"name": f"Wall {i}"}, "version": 1})
    door = {"id": "door_0000000000000001", "kind": "door", "parent_id": walls[0]["id"], "level_id": lvl["id"], "params": {"along": 2, "width": 0.9, "height": 2.1, "sill": 0}, "version": 1}
    window = {"id": "win_00000000000000001", "kind": "window", "parent_id": walls[1]["id"], "level_id": lvl["id"], "params": {"along": 2, "width": 1.2, "height": 1.2, "sill": 1}, "version": 1}
    slab = {"id": "slab_000000000000001", "kind": "slab", "level_id": lvl["id"], "params": {"outline": [[0, 0], [6, 0], [6, 4], [0, 4]], "thickness": 0.25, "offset": 0}, "version": 1}
    col = {"id": "col_00000000000000001", "kind": "column", "level_id": lvl["id"], "params": {"position": [3, 2], "section": {"shape": "rect", "w": 0.4, "d": 0.4}, "height": 3}, "version": 1}
    pipe = {"id": "pipe_000000000000001", "kind": "pipe", "params": {"start": [1, 1, 2.5], "end": [5, 1, 2.5], "od": 0.1683}, "version": 1}
    beam = {"id": "beam_000000000000001", "kind": "beam", "params": {"start": [0.5, 3, 2.8], "end": [5.5, 3, 2.8], "profile": {"shape": "rect", "w": 0.2, "h": 0.3}}, "version": 1}
    return {"seq": 7, "levels": [lvl], "types": [], "elements": [*walls, door, window, slab, col, pipe, beam]}


def test_geometry_every_element_draws():
    m = Model(room())
    parts = all_parts(m)
    assert set(parts) == {e["id"] for e in room()["elements"]}
    for ps in parts.values():
        for p in ps:
            assert p.vertices.shape[1] == 3 and p.faces.max() < len(p.vertices)


def test_wall_volume_and_holes():
    import trimesh

    m = Model(room())
    w2 = m.get("wall_0000000000000002")  # no hosted elements; both ends meet other walls
    v = sum(trimesh.Trimesh(p.vertices, p.faces, process=False).volume for p in element_parts(w2, m))
    # 6 m + 2 × 0.1 m extension (joins), 0.2 thick, 3 high: boxes overlap nothing within one wall
    assert v == pytest.approx(6.2 * 0.2 * 3, rel=1e-6)
    w0 = m.get("wall_0000000000000000")
    v0 = sum(trimesh.Trimesh(p.vertices, p.faces, process=False).volume for p in element_parts(w0, m))
    assert v0 == pytest.approx(6.2 * 0.2 * 3 - 0.9 * 2.1 * 0.2, rel=1e-6)


def test_pipe_and_column_shapes():
    import trimesh

    m = Model(room())
    col = sum(trimesh.Trimesh(p.vertices, p.faces, process=False).volume for p in element_parts(m.get("col_00000000000000001"), m))
    assert col == pytest.approx(0.4 * 0.4 * 3, rel=1e-6)
    pipe = element_parts(m.get("pipe_000000000000001"), m)[0]
    r = np.linalg.norm(pipe.vertices[:, 1:] - [1, 2.5], axis=1)
    assert r.max() == pytest.approx(0.1683 / 2, abs=1e-6)


def _glb_json(data: bytes) -> dict:
    magic, version, _ = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67 and version == 2
    n, kind = struct.unpack("<II", data[12:20])
    assert kind == 0x4E4F534A
    return json.loads(data[20 : 20 + n])


def test_build_files():
    import ifcopenshell
    import trimesh

    read = room()
    read["project_id"] = "00000000-0000-0000-0000-000000000000"
    files = build_files(read, project_name="Test room")
    gj = _glb_json(files["model.glb"])
    ids = {n["extras"]["id"] for n in gj["nodes"] if "extras" in n}
    assert ids == {e["id"] for e in read["elements"]}
    scene = trimesh.load(trimesh.util.wrap_as_stream(files["model.glb"]), file_type="glb", force="scene")
    b = scene.bounds  # glTF axes: y up, so the room's z (0..3) is glTF y
    assert b[1][1] == pytest.approx(3.0, abs=1e-3) and b[0][1] == pytest.approx(-0.25, abs=1e-3)
    graph = json.loads(files["graph.json"])
    assert graph["seq"] == 7 and len(graph["elements"]) == len(read["elements"]) and len(graph["levels"]) == 1
    index = json.loads(files["index.json"])
    assert index["wall_0000000000000000"] == 1
    path = Path(__file__).parent / "_test.ifc"
    path.write_bytes(files["model.ifc"])
    try:
        f = ifcopenshell.open(str(path))
        assert len(f.by_type("IfcWall")) == 4
        assert len(f.by_type("IfcDoor")) == 1 and len(f.by_type("IfcWindow")) == 1
        assert len(f.by_type("IfcSlab")) == 1 and len(f.by_type("IfcColumn")) == 1
        assert len(f.by_type("IfcPipeSegment")) == 1 and len(f.by_type("IfcBeam")) == 1
        assert len(f.by_type("IfcBuildingStorey")) == 1
        assert all(w.Representation is not None for w in f.by_type("IfcWall"))
    finally:
        path.unlink()


def _surface_points(read: dict, ids: list[str], spacing: float, offset: dict[str, np.ndarray] | None = None, noise: float = 0.002, seed: int = 1) -> np.ndarray:
    """Points sampled on elements' surfaces (moved by `offset`), with noise."""
    import trimesh

    rng = np.random.default_rng(seed)
    m = Model(read)
    out = []
    for id in ids:
        for p in element_parts(m.get(id), m):
            mesh = trimesh.Trimesh(p.vertices, p.faces, process=False)
            n = max(200, int(mesh.area / spacing**2))
            pts, _ = trimesh.sample.sample_surface_even(mesh, n, seed=seed)
            out.append(pts + (offset or {}).get(id, 0) + rng.normal(0, noise, pts.shape))
    return np.concatenate(out)


def test_fit_recovers_offsets():
    read = room()
    wall = "wall_0000000000000002"  # (6,4)→(0,4): its left normal points −y
    shift = {wall: np.array([0, 0.02, 0]), "col_00000000000000001": np.array([0.015, -0.01, 0]), "pipe_000000000000001": np.array([0, 0.03, -0.02])}
    pts = _surface_points(read, [wall, "col_00000000000000001", "pipe_000000000000001"], 0.03, shift)
    ops, fitted, skipped = fitmod.fit_model(read, [wall, "col_00000000000000001", "pipe_000000000000001", "door_0000000000000001"], pts)
    assert {s["id"] for s in skipped} == {"door_0000000000000001"}
    by = {o["id"]: o["patch"]["params"] for o in ops if "params" in o["patch"]}
    assert by[wall]["start"][1] == pytest.approx(4.02, abs=0.004)
    assert by[wall]["thickness"] == pytest.approx(0.2, abs=0.004)
    assert by["col_00000000000000001"]["position"] == pytest.approx([3.015, 1.99], abs=0.004)
    assert by["pipe_000000000000001"]["start"][1:] == pytest.approx([1.03, 2.48], abs=0.004)
    assert by["pipe_000000000000001"]["od"] == pytest.approx(0.1683, abs=0.004)
    assert all(f["changed"] for f in fitted)
    assert all(o["if_version"] == 1 for o in ops)
    assert all(o["patch"]["provenance"]["status"] == "observed" for o in ops)


def test_fit_leaves_good_elements():
    read = room()
    wall = "wall_0000000000000002"
    pts = _surface_points(read, [wall], 0.03, noise=0.001)
    ops, fitted, _ = fitmod.fit_model(read, [wall], pts)
    assert fitted[0]["changed"] is False
    assert not any("params" in o["patch"] for o in ops)


def test_heatmap_known_offset_and_encoding():
    read = room()
    wall = "wall_0000000000000002"
    pts = _surface_points(read, [wall], 0.05, {wall: np.array([0, 0.01, 0])}, noise=0.0)
    far = np.array([[3, 2, 10.0]])  # nothing within 1 m
    pts = np.concatenate([pts, far])
    s = heat.Surfaces(read)
    dist, cats = heat.compute(s, pts)
    st = heat.heat_stats(dist, cats)
    # the long faces moved 10 mm off; the end faces that moved along themselves stay ~0 — so the median is ≤ 10 mm
    assert 0 <= st["p50_mm"] <= 10.5 and st["p95_mm"] == pytest.approx(10, abs=1.0)
    assert np.isinf(dist[-1]) and cats[-1] == 0
    # walls are structure; points along the wall's foot sit as close to the floor slab (floor/ground)
    assert set(np.unique(cats[:-1])) <= {1, 2} and (cats[:-1] == 2).mean() > 0.9
    rec = np.frombuffer(heat.encode(dist, cats), dtype=np.uint8).reshape(-1, 3)
    q = rec[:, 0].astype(int) | (rec[:, 1].astype(int) << 8)
    assert q[-1] == 0xFFFF
    assert np.allclose(q[:-1] * 1e-4, dist[:-1], atol=1e-4)
    h = heat.histograms(dist, cats)
    assert sum(h["all"]) == len(pts) and len(h["all"]) == len(h["edges_mm"]) - 1


def test_point_triangle_distance():
    a, b, c = np.array([[0.0, 0, 0]]), np.array([[1.0, 0, 0]]), np.array([[0.0, 1, 0]])
    cases = {(0.2, 0.2, 0.5): 0.5, (-1.0, 0, 0): 1.0, (2.0, 0, 0): 1.0, (0.5, -1, 0): 1.0, (1.0, 1, 0): np.sqrt(0.5)}
    for p, want in cases.items():
        got = heat.point_triangle_distance(np.array([p]), a, b, c)[0]
        assert got == pytest.approx(want, abs=1e-9)


def test_potree_default_decode():
    meta = {"encoding": "DEFAULT", "scale": [0.001, 0.001, 0.001], "offset": [10, 20, 30], "points": 3,
            "attributes": [{"name": "position", "size": 12, "type": "int32"}, {"name": "intensity", "size": 2, "type": "uint16"},
                           {"name": "classification", "size": 1, "type": "uint8"}]}
    ints = np.array([[0, 0, 0], [1000, 2000, 3000], [-500, 0, 1]], dtype="<i4")
    rec = b"".join(ints[i].tobytes() + struct.pack("<H", 7) + bytes([i + 3]) for i in range(3))
    xyz, cls = decode_octree(meta, rec)
    assert np.allclose(xyz, [[10, 20, 30], [11, 22, 33], [9.5, 20, 30.001]])
    assert cls.tolist() == [3, 4, 5]
    with pytest.raises(ValueError):
        decode_octree({**meta, "encoding": "BROTLI"}, rec)


def test_wall_frame():
    m = Model(room())
    f = wall_frame(m.get("wall_0000000000000000"), m)
    assert f.length == 6 and f.half == pytest.approx(0.1) and (f.base, f.top) == (0, 3)
