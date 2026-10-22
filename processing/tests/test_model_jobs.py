"""The model jobs' run() against an in-memory stand-in for the worker API (ma_proc.api.Api)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ma_proc.model import build, fit, heatmap  # noqa: E402
from test_model import _surface_points, room  # noqa: E402

PID = "11111111-2222-3333-4444-555555555555"


class FakeApi:
    def __init__(self, read: dict):
        self.read = read
        self.r2: dict[str, bytes] = {}
        self.revisions: list[dict] = []
        self.files: list[dict] = []
        self.messages: list[dict] = []
        self.ops: list[dict] = []
        self.base = None
        self.events_sent: list[dict] = []
        self.scans: list[dict] = []
        self.jobs: list[dict] = []

    # jobs and project
    def job(self, job_id, **fields):
        self.jobs.append(fields)

    def project(self, pid):
        return {"project": {"id": pid, "name": "Test"}, "scans": self.scans, "revisions": self.revisions, "files": self.files}

    def model(self, pid):
        return json.loads(json.dumps(self.read))

    def model_ops(self, pid, ops, *, note=None, author=None):
        self.ops.append({"ops": ops, "note": note, "author": author})
        return {"seq": self.read["seq"] + 1}

    def model_base(self, pid, **base):
        self.base = base
        return {"base": base}

    def add_revision(self, pid, **fields):
        r = {"number": len(self.revisions) + 1, "heatmaps": {}, **fields}
        self.revisions.append(r)
        return r

    def update_revision(self, pid, number, **fields):
        r = self.revisions[number - 1]
        r.update(fields)
        return r

    def add_file(self, pid, r2_key, **kw):
        assert r2_key in self.r2 and r2_key.startswith(f"projects/{pid}/")
        f = {"id": f"file{len(self.files)}", "r2_key": r2_key, **kw}
        self.files.append(f)
        return f

    def message(self, pid, text, *, role="system", body=None):
        self.messages.append(body or {"text": text})
        return {"id": len(self.messages)}

    def set_live_heatmap(self, pid, scan_id, entry):
        self.live = {**getattr(self, "live", {}), scan_id: entry}
        return entry

    def events(self, pid, *events):
        self.events_sent += events

    # R2
    def upload_bytes(self, data, key, **kw):
        self.r2[key] = bytes(data)
        return key

    def upload_json(self, obj, key):
        return self.upload_bytes(json.dumps(obj).encode(), key)

    def exists(self, key, **kw):
        return key in self.r2

    def download(self, key, dest, **kw):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.r2[key])
        return dest


def potree_layer(api: FakeApi, prefix: str, pts: np.ndarray) -> None:
    """A DEFAULT-encoded layer: position int32×3 (1 mm), then a classification byte."""
    scale, offset = 0.001, pts.min(axis=0)
    ints = np.round((pts - offset) / scale).astype("<i4")
    rec = np.zeros((len(pts), 13), dtype=np.uint8)
    rec[:, :12] = ints.view(np.uint8).reshape(-1, 12)
    rec[:, 12] = 3
    meta = {"version": "2.0", "encoding": "DEFAULT", "points": len(pts), "scale": [scale] * 3, "offset": offset.tolist(),
            "attributes": [{"name": "position", "size": 12, "type": "int32"}, {"name": "classification", "size": 1, "type": "uint8"}]}
    api.r2[f"{prefix}/metadata.json"] = json.dumps(meta).encode()
    api.r2[f"{prefix}/octree.bin"] = rec.tobytes()


def test_build_run():
    api = FakeApi(room())
    out = build.run(api, {"id": "j1", "project_id": PID, "input": {"title": "First"}}, {"project": {"name": "Test"}})
    rev = api.revisions[0]
    assert rev["status"] == "ready" and rev["model_seq"] == 7 and rev["ifc_key"].endswith("model.ifc")
    assert {f["name"] for f in api.files} == {"Test r1.ifc", "Test r1.glb"}
    assert api.base["seq"] == 7 and api.base["glb"] == "model/builds/7/model.glb" and api.base["view"] is None
    assert json.loads(api.r2[f"projects/{PID}/model/builds/7/index.json"])["wall_0000000000000000"] == 1
    assert "IFC opens in Revit" in api.messages[0]["text"]
    assert out["revision"] == 1


def test_fit_run_as_the_person():
    read = room()
    api = FakeApi(read)
    wall = "wall_0000000000000002"
    pts = _surface_points(read, [wall], 0.03, {wall: np.array([0, 0.02, 0])})
    prefix = f"projects/{PID}/scans/s1/potree"
    potree_layer(api, prefix, pts)
    scan = {"id": "s1", "status": "ready", "viewer": {"full": {"potree_prefix": prefix}}}
    out = fit.run(api, {"id": "j2", "project_id": PID, "input": {"element_ids": [wall], "by": "u-123"}}, {"scans": [scan]})
    assert out["fitted"][0]["changed"] and out["seq"] == 8
    assert api.ops[0]["author"] == {"kind": "user", "id": "user:u-123", "name": "Fit to scan"}


def test_heatmap_run_revision_attr_pages():
    read = room()
    api = FakeApi(read)
    build.run(api, {"id": "j1", "project_id": PID, "input": {}}, {"project": {"name": "Test"}})
    wall = "wall_0000000000000002"
    pts = _surface_points(read, [wall], 0.05, {wall: np.array([0, 0.01, 0])}, noise=0.0)
    prefix = f"projects/{PID}/scans/s1/potree"
    potree_layer(api, prefix, pts)
    api.scans = [{"id": "s1", "name": "Scan", "status": "ready", "viewer": {"full": {"potree_prefix": prefix}}}]
    out = heatmap.run(api, {"id": "j3", "project_id": PID, "input": {"revision": 1}}, {"scans": api.scans})
    entry = api.revisions[0]["heatmaps"]["s1"]
    assert entry["status"] == "ready" and entry["format"] == "attr"
    assert entry["layer"] == "scans/s1/potree/metadata.json"
    index = json.loads(api.r2[f"projects/{PID}/{entry['attr']}"])
    assert index["points"] == len(pts) and index["octree_bytes_per_point"] == 13 and index["bytes_per_point"] == 3
    page = api.r2[f"projects/{PID}/{index['base']}{index['pages'][0]}"]
    assert len(page) == 3 * len(pts)
    # decode the first records as heatAttr.ts decodeAttr does
    rec = np.frombuffer(page, dtype=np.uint8).reshape(-1, 3)
    dev = (rec[:, 0].astype(int) | (rec[:, 1].astype(int) << 8)) * 1e-4
    assert np.percentile(dev, 95) == np.float64(np.percentile(dev, 95)) and 0.009 < np.percentile(dev, 95) < 0.011
    assert entry["stats"]["distances_key"].endswith("distances.json")
    assert api.revisions[0]["heatmap"]["scan_id"] == "s1"
    assert out["heatmaps"]["s1"]["stats"]["points"] == len(pts)


def test_heatmap_live_emits():
    read = room()
    api = FakeApi(read)
    pts = _surface_points(read, ["wall_0000000000000002"], 0.1, noise=0.0)
    prefix = f"projects/{PID}/scans/s1/potree"
    potree_layer(api, prefix, pts)
    api.scans = [{"id": "s1", "status": "ready", "viewer": {"full": {"potree_prefix": prefix}}}]
    out = heatmap.run(api, {"id": "j4", "project_id": PID, "input": {"live": True}}, {"scans": api.scans})
    assert out["live"] and api.events_sent[0]["type_"] == "heatmap_live"
    assert any(k.endswith("/heatmaps/s1/live-7/index.json") for k in api.r2)
    assert api.live["s1"]["format"] == "attr" and api.live["s1"]["seq"] == 7
