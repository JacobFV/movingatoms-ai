"""The `build` job (§17.5): a checkpoint of the live model.

Writes under projects/<pid>/model/builds/<seq>/: model.glb (one node per element, as the viewer reads it), graph.json
(ModelGraph), index.json ({element id: version}) and model.ifc. Creates the revision (building → ready), registers
model.ifc and model.glb as deliverables, makes the build the live model's base, and says so in the chat.
The viewer draws model.glb when a base has no view.glb (view: null), so no batched view is written.
Explicit experimental native requests additionally require acknowledged hypotheses and a configured runtime bundle.
All artifacts and independent native evidence are staged before uploads; native opening/regeneration stay unverified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
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


def _experimental_native_files(read: dict, load_mesh, bundle: Path) -> tuple[dict[str, bytes], dict]:
    """Stage all verified native bytes/evidence before any remote publication."""
    from .rvt_export import export_experimental

    with tempfile.TemporaryDirectory(prefix="ma-build-rvt-") as temporary:
        output = Path(temporary) / "native"
        result = export_experimental(read, bundle, output, load_mesh=load_mesh, acknowledge_hypotheses=True)
        candidate = Path(result["candidate"]).read_bytes()
        digest = hashlib.sha256(candidate).hexdigest()
        report = json.loads(Path(result["report"]).read_bytes())
        if (result.get("production_native_export") is not False or result.get("autodesk_acceptance") != "not_tested"
                or result.get("candidate_sha256") != digest or report.get("candidate_sha256") != digest
                or report.get("status") != "verified_research_candidate" or report.get("production_native_export") is not False
                or report.get("autodesk_acceptance") != "not_tested"):
            raise ValueError("experimental native candidate qualification/hash mismatch")
        hashes = report.get("validation_reports", {})
        if not isinstance(hashes, dict) or not {"transport.json", "metadata.json", "native.json"} <= set(hashes):
            raise ValueError("experimental native independent validation reports missing")
        checks = {}
        for name, expected in hashes.items():
            if not isinstance(name, str) or Path(name).name != name or name in (".", ".."):
                raise ValueError("invalid native validation evidence filename")
            data = (output / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("native validation evidence hash mismatch")
            checks[name] = json.loads(data)
        evidence = {"schema": "ma-experimental-native-validation/1", "experimental": True,
                    "candidate_sha256": digest, "autodesk_acceptance": "not_tested",
                    "native_opening": "not_tested", "regeneration": "not_tested", "production_native_export": False,
                    "run": report, "validation_reports": checks}
        files = {"model.experimental.rvt": candidate,
                 "model.experimental.validation.json": json.dumps(evidence, allow_nan=False, indent=2).encode()}
        return files, {"experimental": True, "candidate_sha256": digest, "autodesk_acceptance": "not_tested",
                       "native_opening": "not_tested", "regeneration": "not_tested", "production_native_export": False}


CONTENT_TYPES = {"model.glb": "model/gltf-binary", "graph.json": "application/json", "index.json": "application/json", "model.ifc": "application/x-step", "model.experimental.rvt": "application/octet-stream", "model.experimental.validation.json": "application/json"}


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
        native_requested = inp.get("experimental_native_rvt", False)
        acknowledged = inp.get("acknowledge_native_hypotheses", False)
        if type(native_requested) is not bool or type(acknowledged) is not bool:
            raise ValueError("experimental native flags must be booleans")
        bundle = None
        if native_requested:
            if not acknowledged:
                raise ValueError("experimental native RVT requires acknowledge_native_hypotheses=true")
            configured = os.environ.get("MA_RVT_RUNTIME_BUNDLE", "").strip()
            if not configured:
                raise ValueError("experimental native RVT requires MA_RVT_RUNTIME_BUNDLE")
            bundle = Path(configured)
            if not (bundle / "run.py").is_file():
                raise ValueError("experimental native runtime bundle run.py is missing")
        api.job(job["id"], stage="building geometry", progress=0.2)
        load_mesh = mesh_loader(api, pid)
        files = build_files(read, project_name=name, load_mesh=load_mesh)
        native_meta = None
        if native_requested:
            api.job(job["id"], stage="verifying experimental native RVT", progress=0.45)
            native_files, native_meta = _experimental_native_files(read, load_mesh, bundle)
            files.update(native_files)
        base = f"projects/{pid}/model/builds/{seq}"
        api.job(job["id"], stage="saving", progress=0.7)
        keys = {}
        for fname, data in files.items():
            keys[fname] = api.upload_bytes(data, f"{base}/{fname}", content_type=CONTENT_TYPES[fname])
        notes = (inp.get("notes") or "").strip()
        file_note = "Files: model.glb and IFC 4 (IFC opens in Revit)."
        if native_requested:
            file_note += " Experimental native RVT and its validation evidence are included. Native opening and regeneration are unverified; this is not a production-qualified native export."
        notes = (notes + "\n\n" if notes else "") + file_note
        api.update_revision(pid, number, status="ready", model_seq=seq, glb_key=keys["model.glb"], graph_key=keys["graph.json"], ifc_key=keys["model.ifc"], notes=notes)
        stem = f"{name} r{number}".replace("/", "-")
        ifc_file = api.add_file(pid, keys["model.ifc"], kind="deliverable", name=f"{stem}.ifc", content_type="application/x-step", meta={"revision": number, "seq": seq})
        glb_file = api.add_file(pid, keys["model.glb"], kind="deliverable", name=f"{stem}.glb", content_type="model/gltf-binary", meta={"revision": number, "seq": seq})
        deliverables = [ifc_file, glb_file]
        if native_requested:
            validation_file = api.add_file(pid, keys["model.experimental.validation.json"], kind="deliverable",
                name=f"{stem}.experimental.validation.json", content_type="application/json",
                meta={"revision": number, "seq": seq, **native_meta, "evidence_for_key": keys["model.experimental.rvt"]})
            native_file = api.add_file(pid, keys["model.experimental.rvt"], kind="deliverable",
                name=f"{stem}.experimental.rvt", content_type="application/octet-stream",
                meta={"revision": number, "seq": seq, **native_meta, "validation_file_id": validation_file["id"],
                      "validation_key": keys["model.experimental.validation.json"]})
            deliverables += [native_file, validation_file]
        rel = lambda k: k[len(f"projects/{pid}/"):]  # noqa: E731 - keys under the viewer's assetBase
        api.model_base(pid, seq=seq, glb=rel(keys["model.glb"]), view=None, graph=rel(keys["graph.json"]), index=rel(keys["index.json"]))
        count = len([e for e in read["elements"] if not e.get("deleted")])
        api.message(pid, "", body={
            "text": f"Revision {number} is ready: {count} element{'s' if count != 1 else ''} as IFC and GLB. IFC opens in Revit."
                    + (" Experimental native RVT and validation evidence are attached; native opening and regeneration remain unverified." if native_requested else ""),
            "blocks": [{"type": "file", "file_id": file["id"]} for file in deliverables],
        })
        api.job(job["id"], stage="done", progress=1.0)
        return {"revision": number, "seq": seq, "elements": count, "files": [file["id"] for file in deliverables], "keys": keys,
                **({"experimental_native_rvt": True, "native_validation": native_meta} if native_requested else {})}
    except Exception as e:
        try:
            api.update_revision(pid, number, status="error", notes=f"The build failed: {e}"[:2000])
        except Exception:  # noqa: BLE001
            log.exception("could not mark revision %s failed", number)
        raise
