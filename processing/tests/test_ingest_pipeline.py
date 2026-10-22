"""The whole ingest job on a synthetic room (floor, ceiling, four walls, a column, a pipe, a box of equipment), with a
fake site API: stages in order, labels found, a Potree layer and two pictures uploaded, the scan ready."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from test_ingest_fakeapi import FakeApi
from ma_proc.ingest import classify, job as ingest, potree

RNG = np.random.default_rng(4)


def plane(n, ax, ay, val, axis):
    a = RNG.random(n) * ax
    b = RNG.random(n) * ay
    v = np.full(n, val) + RNG.normal(0, 0.002, n)
    return {"z": np.column_stack([a, b, v]), "x": np.column_stack([v, a, b]), "y": np.column_stack([a, v, b])}[axis]


def room() -> tuple[np.ndarray, np.ndarray]:
    W, D, H = 8.0, 6.0, 3.0
    parts, labs = [], []
    def add(p, l):
        parts.append(p)
        labs.append(np.full(len(p), l))
    add(plane(120_000, W, D, 0.0, "z"), classify.FLOOR)
    add(plane(120_000, W, D, H, "z"), classify.CEILING)
    add(plane(60_000, D, H, 0.0, "x")[:, [0, 1, 2]], classify.WALL)
    add(plane(60_000, D, H, W, "x"), classify.WALL)
    add(plane(70_000, W, H, 0.0, "y"), classify.WALL)
    add(plane(70_000, W, H, D, "y"), classify.WALL)
    # a round column, 0.2 m radius, floor to ceiling
    t = RNG.random(20_000) * 2 * np.pi
    add(np.column_stack([2 + 0.2 * np.cos(t), 2 + 0.2 * np.sin(t), RNG.random(20_000) * H]), classify.COLUMN)
    # a pipe, 0.08 m radius, along x at 2.5 m
    t = RNG.random(15_000) * 2 * np.pi
    add(np.column_stack([1 + RNG.random(15_000) * 5, 4.5 + 0.08 * np.cos(t), 2.5 + 0.08 * np.sin(t)]), classify.PIPE)
    # a box of equipment on the floor
    add(RNG.random((20_000, 3)) * [1.2, 0.8, 1.0] + [5, 1, 0], classify.EQUIPMENT)
    return np.concatenate(parts), np.concatenate(labs)


@pytest.fixture(scope="module")
def ingested(tmp_path_factory):
    if not shutil.which("PotreeConverter"):
        try:
            potree.converter()
        except RuntimeError:
            pytest.skip("PotreeConverter isn't installed")
    tmp = tmp_path_factory.mktemp("ingest")
    xyz, truth = room()
    rgb = (RNG.random((len(xyz), 3)) * 255).astype(int)
    src = tmp / "room.xyz"
    np.savetxt(src, np.column_stack([xyz + [500000, 4000000, 12], rgb]), fmt="%.4f %.4f %.4f %d %d %d")
    api = FakeApi(tmp / "r2", {"projects/p/sources/f/room.xyz": src})
    j = {"id": "j", "project_id": "p", "type": "ingest", "input": {"scan_id": "s", "file_id": "f", "r2_key": "projects/p/sources/f/room.xyz"}}
    res = ingest.run(api, j, {"job": j}, work=tmp / "work")
    return api, res, tmp


def test_stages_in_order(ingested):
    api, res, _ = ingested
    statuses = [c[2]["status"] for c in api.calls if c[0] == "scan"]
    order = ["inspecting", "decoding", "labelling", "converting", "overview", "ready"]
    seen = [s for i, s in enumerate(statuses) if i == 0 or s != statuses[i - 1]]
    assert seen == order


def test_scan_fields(ingested):
    api, res, _ = ingested
    s = api.scans["s"]
    assert s["status"] == "ready" and s["point_count"] == res["points"]
    b = s["bounds"]
    assert np.allclose(np.array(b["max"]) - np.array(b["min"]), [8, 6, 3], atol=0.05)
    brief = s["brief"]
    assert brief["frame"]["offset"][0] > 499_000  # georeferenced coordinates moved near the origin
    kinds = [l["kind"] for l in brief["levels_guess"]]
    assert kinds[0] == "floor" and kinds[-1] == "ceiling"
    assert 40 <= brief["footprint_m2"] <= 60
    assert s["viewer"]["overview"]["has_labels"]
    assert s["viewer"]["full"]["potree_prefix"] == "projects/p/scans/s/potree" == s["potree_prefix"]


def test_labels_are_mostly_right(ingested):
    api, res, _ = ingested
    c = {int(k): v for k, v in res["labels"].items()}
    total = sum(c.values())
    assert c.get(classify.FLOOR, 0) > 0.12 * total
    assert c.get(classify.CEILING, 0) > 0.12 * total
    assert c.get(classify.WALL, 0) > 0.25 * total
    assert c.get(classify.COLUMN, 0) > 0.5 * 20_000
    assert c.get(classify.PIPE, 0) > 0.5 * 15_000


def test_outputs_uploaded(ingested):
    api, _, tmp = ingested
    prefix = tmp / "r2" / "projects/p/scans/s/potree-overview"
    meta = json.loads((prefix / "metadata.json").read_text())
    assert meta["version"] == "2.0"
    assert {"position", "classification", "rgb"} <= {a["name"] for a in meta["attributes"]}
    assert (prefix / "octree.bin").stat().st_size > 0
    assert meta["encoding"] == "DEFAULT"
    assert (tmp / "r2" / "projects/p/scans/s/potree/metadata.json").exists()
    assert (tmp / "r2" / "projects/p/scans/s/labelled.las").stat().st_size > 0
    names = sorted(f["name"] for f in api.files)
    assert names == ["overview-iso_ne.png", "overview-top.png"]
    assert set(api.scans["s"]["overview"]) == {"top", "iso_ne"}
