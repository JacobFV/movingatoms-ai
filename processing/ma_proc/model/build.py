"""The `build` job (§17.5): a checkpoint of the live model.

Writes under projects/<pid>/model/builds/<seq>/: model.glb (one node per element, as the viewer reads it), graph.json
(ModelGraph), index.json ({element id: version}) and model.ifc. Creates the revision (building → ready), registers
model.ifc and model.glb as deliverables, makes the build the live model's base, and says so in the chat.
The viewer draws model.glb when a base has no view.glb (view: null), so no batched view is written.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .geometry import Model, all_parts, ifc_class_of
from .glb import read_glb_parts, write_glb
from .ifc import write_ifc

log = logging.getLogger(__name__)

GRAPH_SCHEMA = "ma-model-graph/1"


def mesh_loader(api: Any, pid: str):
    cache: dict[str, list] = {}

    def load(sha: str):
        if sha not in cache:
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as d:
                p = api.download(f"projects/{pid}/model/meshes/{sha}.glb", Path(d) / f"{sha}.glb")
                cache[sha] = read_glb_parts(p.read_bytes())
        return cache[sha]

    return load


def node_extras(e: dict, m: Model) -> dict:
    lvl_id = e.get("level_id") or (m.get(e.get("parent_id")) or {}).get("level_id")
    lvl = m.get(lvl_id)
    return {
        "id": e["id"],
        "kind": e.get("kind"),
        "ifc_class": ifc_class_of(e),
        "name": (e.get("props") or {}).get("name"),
        "level": lvl_id,
        "level_name": ((lvl or {}).get("props") or {}).get("name"),
        "version": int(e.get("version") or 0),
    }


def build_files(read: dict, *, project_name: str, load_mesh=None) -> dict[str, bytes]:
    """The build's files from a model read: {'model.glb', 'graph.json', 'index.json', 'model.ifc'} → bytes."""
    m = Model(read)
    parts = all_parts(m, load_mesh)
    nodes = [{"name": (e.get("props") or {}).get("name") or id, "extras": node_extras(e, m), "parts": parts[id]} for id, e in m.elements.items() if id in parts]
    graph = {
        "schema": GRAPH_SCHEMA,
        "project_id": read.get("project_id"),
        "seq": m.seq,
        "levels": [e for e in m.elements.values() if e.get("kind") == "level"],
        "types": list(m.types.values()),
        "elements": [e for e in m.elements.values() if e.get("kind") != "level"],
    }
    index = {id: int(e.get("version") or 0) for id, e in m.elements.items()}
    return {
        "model.glb": write_glb(nodes),
        "graph.json": json.dumps(graph, separators=(",", ":")).encode(),
        "index.json": json.dumps(index, separators=(",", ":")).encode(),
        "model.ifc": write_ifc(m, parts, project_name=project_name),
    }


CONTENT_TYPES = {"model.glb": "model/gltf-binary", "graph.json": "application/json", "index.json": "application/json", "model.ifc": "application/x-step"}


def run(api: Any, job: dict, claim: dict) -> dict:
    pid = job["project_id"]
    inp = job.get("input") or {}
    project = claim.get("project") or {}
    name = project.get("name") or "Project"
    api.job(job["id"], stage="reading the model", progress=0.05)
    read = api.model(pid)
    read["project_id"] = pid
    seq = int(read.get("seq") or 0)
    if not read.get("elements"):
        raise ValueError("the model has no elements yet; nothing to build")
    rev = api.add_revision(pid, title=inp.get("title") or f"Model at change {seq}", notes=inp.get("notes") or None, status="building", model_seq=seq)
    number = rev["number"]
    try:
        api.job(job["id"], stage="building geometry", progress=0.2)
        files = build_files(read, project_name=name, load_mesh=mesh_loader(api, pid))
        base = f"projects/{pid}/model/builds/{seq}"
        api.job(job["id"], stage="saving", progress=0.7)
        keys = {}
        for fname, data in files.items():
            keys[fname] = api.upload_bytes(data, f"{base}/{fname}", content_type=CONTENT_TYPES[fname])
        notes = (inp.get("notes") or "").strip()
        notes = (notes + "\n\n" if notes else "") + "Files: model.glb and IFC 4 (IFC opens in Revit; a native .rvt can't be produced here)."
        api.update_revision(pid, number, status="ready", model_seq=seq, glb_key=keys["model.glb"], graph_key=keys["graph.json"], ifc_key=keys["model.ifc"], notes=notes)
        stem = f"{name} r{number}".replace("/", "-")
        ifc_file = api.add_file(pid, keys["model.ifc"], kind="deliverable", name=f"{stem}.ifc", content_type="application/x-step", meta={"revision": number, "seq": seq})
        glb_file = api.add_file(pid, keys["model.glb"], kind="deliverable", name=f"{stem}.glb", content_type="model/gltf-binary", meta={"revision": number, "seq": seq})
        rel = lambda k: k[len(f"projects/{pid}/"):]  # noqa: E731 - keys under the viewer's assetBase
        api.model_base(pid, seq=seq, glb=rel(keys["model.glb"]), view=None, graph=rel(keys["graph.json"]), index=rel(keys["index.json"]))
        count = len([e for e in read["elements"] if not e.get("deleted")])
        api.message(pid, "", body={
            "text": f"Revision {number} is ready: {count} element{'s' if count != 1 else ''} as IFC and GLB. IFC opens in Revit.",
            "blocks": [{"type": "file", "file_id": ifc_file["id"]}, {"type": "file", "file_id": glb_file["id"]}],
        })
        api.job(job["id"], stage="done", progress=1.0)
        return {"revision": number, "seq": seq, "elements": count, "files": [ifc_file["id"], glb_file["id"]], "keys": keys}
    except Exception as e:
        try:
            api.update_revision(pid, number, status="error", notes=f"The build failed: {e}"[:2000])
        except Exception:  # noqa: BLE001
            log.exception("could not mark revision %s failed", number)
        raise
