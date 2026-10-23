"""IFC4 export of the model: project, site, building, a storey per level, each element as its ifc_class with its
geometry as a triangulated face set (absolute working-frame coordinates, metres), names and properties.
The working-frame coordinates and project units are metres."""
from __future__ import annotations

import json
from typing import Any

import numpy as np

from .geometry import Model, Part, ifc_class_of


def _entity_class(name: str) -> str:
    """The class if IFC4 has it (and it isn't abstract), else a proxy."""
    import ifcopenshell

    try:
        decl = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC4").declaration_by_name(name)
        if decl is not None and not decl.is_abstract():
            return name
    except Exception:  # noqa: BLE001 - not a class in this schema
        pass
    return "IfcBuildingElementProxy"


def _prop_value(v: Any) -> Any:
    if isinstance(v, bool) or isinstance(v, (int, float)) or isinstance(v, str):
        return v
    return json.dumps(v, separators=(",", ":"))[:2000]


def write_ifc(m: Model, parts: dict[str, list[Part]], *, project_name: str, author: str = "Moving Atoms") -> bytes:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.api.aggregate
    import ifcopenshell.api.context
    import ifcopenshell.api.geometry
    import ifcopenshell.api.project
    import ifcopenshell.api.pset
    import ifcopenshell.api.root
    import ifcopenshell.api.spatial
    import ifcopenshell.api.unit

    f = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name=project_name)
    # The no-argument API defaults to millimetres. Our levels and mesh input
    # share an SI-metre contract, so assign units explicitly.
    units = [ifcopenshell.api.unit.add_si_unit(f, unit_type=kind)
             for kind in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT")]
    ifcopenshell.api.unit.assign_unit(f, units=units)
    model_ctx = ifcopenshell.api.context.add_context(f, context_type="Model")
    body = ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_ctx)
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name=project_name)
    ifcopenshell.api.aggregate.assign_object(f, relating_object=project, products=[site])
    ifcopenshell.api.aggregate.assign_object(f, relating_object=site, products=[building])

    storeys: dict[str, Any] = {}
    levels = sorted(m.levels, key=lambda l: float((l.get("params") or {}).get("elevation") or 0))
    for lvl in levels:
        st = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=(lvl.get("props") or {}).get("name") or lvl["id"])
        st.Elevation = float((lvl.get("params") or {}).get("elevation") or 0)
        st.LongName = lvl["id"]
        ifcopenshell.api.aggregate.assign_object(f, relating_object=building, products=[st])
        storeys[lvl["id"]] = st
    default_storey = None
    if not storeys:
        default_storey = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name="Level 1")
        default_storey.Elevation = 0.0
        ifcopenshell.api.aggregate.assign_object(f, relating_object=building, products=[default_storey])

    for id, e in m.elements.items():
        if e.get("kind") == "level":
            continue
        cls = _entity_class(ifc_class_of(e))
        if cls in ("IfcOpeningElement",):  # an opening is a void, not a product to draw
            continue
        props = e.get("props") or {}
        el = ifcopenshell.api.root.create_entity(f, ifc_class=cls, name=props.get("name") or f"{e.get('kind')} {id[-6:]}")
        if hasattr(el, "Tag"):
            el.Tag = id
        host = m.get(e.get("parent_id"))
        storey = storeys.get(e.get("level_id") or (host or {}).get("level_id") or "") or default_storey or next(iter(storeys.values()), None)
        if storey is not None:
            ifcopenshell.api.spatial.assign_container(f, relating_structure=storey, products=[el])
        ifcopenshell.api.geometry.edit_object_placement(f, product=el)  # identity: the geometry is in absolute coordinates
        ps = parts.get(id) or []
        if ps:
            # one face set per element (the API wants items of equal shape): parts merged
            vs, fs, base = [], [], 0
            for p in ps:
                vs.append(np.asarray(p.vertices, dtype=float))
                fs.append(np.asarray(p.faces, dtype=np.int64) + base)
                base += len(p.vertices)
            verts = [[tuple(map(float, v)) for v in np.concatenate(vs)]]
            faces = [[[int(i) for i in tri] for tri in np.concatenate(fs)]]
            rep = ifcopenshell.api.geometry.add_mesh_representation(f, context=body, vertices=verts, faces=faces)
            ifcopenshell.api.geometry.assign_representation(f, product=el, representation=rep)
        pset_props = {"ElementId": id, "Kind": str(e.get("kind")), "Version": int(e.get("version") or 0)}
        status = (e.get("provenance") or {}).get("status")
        if status:
            pset_props["Provenance"] = str(status)
        for k, v in props.items():
            if k not in ("name", "appearance") and v is not None:
                pset_props[str(k)[:60]] = _prop_value(v)
        pset = ifcopenshell.api.pset.add_pset(f, product=el, name="MovingAtoms_Element")
        ifcopenshell.api.pset.edit_pset(f, pset=pset, properties=pset_props)
    return f.to_string().encode()
