"""model.glb as the viewer reads it (engine.ts prepareModel): one node per element whose glTF `extras` (three.js
userData) carry {id, kind, ifc_class, name, level, level_name, version}, its parts as child nodes with a mesh each,
materials named after the part's look. glTF is +Y up: a working-frame point (x, y, z) is written as (x, z, −y)."""
from __future__ import annotations

import json
import struct
from typing import Any

import numpy as np

from .geometry import GLTF_TO_WORK, Part

# packages/model looks.ts HINT_LOOKS: name, sRGB colour, roughness, metallic, alpha
LOOKS: dict[str, tuple[str, tuple[float, float, float], float, float, float]] = {
    "wall": ("Plaster, painted", (0.86, 0.85, 0.82), 0.92, 0, 1),
    "slab": ("Concrete", (0.64, 0.63, 0.6), 0.9, 0, 1),
    "ceiling": ("Ceiling, painted", (0.92, 0.92, 0.9), 0.95, 0, 1),
    "roof": ("Roof membrane", (0.36, 0.36, 0.37), 0.85, 0, 1),
    "column": ("Concrete", (0.68, 0.67, 0.64), 0.88, 0, 1),
    "beam": ("Steel, painted", (0.5, 0.52, 0.55), 0.55, 0, 1),
    "pipe": ("Steel pipe", (0.62, 0.63, 0.64), 0.5, 0.3, 1),
    "insulation": ("Insulation cladding", (0.8, 0.81, 0.82), 0.35, 0.85, 1),
    "duct": ("Galvanised steel", (0.72, 0.73, 0.74), 0.4, 0.85, 1),
    "frame": ("Frame, aluminium", (0.55, 0.56, 0.58), 0.4, 0.7, 1),
    "leaf": ("Door leaf, timber", (0.62, 0.48, 0.33), 0.7, 0, 1),
    "glass": ("Glass", (0.78, 0.86, 0.9), 0.05, 0, 0.25),
    "mesh": ("Default", (0.8, 0.8, 0.8), 0.9, 0, 1),
}

WORK_TO_GLTF = GLTF_TO_WORK.T  # orthonormal: the inverse is the transpose


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def flat(part: Part) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unwelded triangles with face normals (flat shading, as the kernel's quads are), in glTF axes."""
    tri = part.vertices[part.faces]  # (M, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    keep = ln[:, 0] > 1e-12
    tri, n = tri[keep], n[keep] / ln[keep]
    pos = tri.reshape(-1, 3) @ WORK_TO_GLTF.T
    nor = np.repeat(n, 3, axis=0) @ WORK_TO_GLTF.T
    idx = np.arange(len(pos), dtype=np.uint32)
    return pos.astype(np.float32), nor.astype(np.float32), idx


def write_glb(elements: list[dict[str, Any]], *, generator: str = "Moving Atoms processing") -> bytes:
    """elements: [{extras: {...}, name, parts: [Part]}] → GLB bytes."""
    gltf: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": generator},
        "scene": 0,
        "scenes": [{"nodes": []}],
        "nodes": [],
        "meshes": [],
        "materials": [],
        "accessors": [],
        "bufferViews": [],
        "buffers": [],
    }
    blob = bytearray()
    mats: dict[str, int] = {}

    def material(hint: str) -> int:
        if hint not in mats:
            name, rgb, rough, metal, alpha = LOOKS.get(hint, LOOKS["mesh"])
            m: dict[str, Any] = {
                "name": name,
                "pbrMetallicRoughness": {"baseColorFactor": [*(_srgb_to_linear(c) for c in rgb), alpha], "metallicFactor": metal, "roughnessFactor": rough},
                "doubleSided": False,
            }
            if alpha < 1:
                m["alphaMode"] = "BLEND"
            mats[hint] = len(gltf["materials"])
            gltf["materials"].append(m)
        return mats[hint]

    def view(data: bytes, target: int) -> int:
        while len(blob) % 4:
            blob.append(0)
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)
        return len(gltf["bufferViews"]) - 1

    def accessor(arr: np.ndarray, kind: str, comp: int, target: int, minmax: bool = False) -> int:
        acc: dict[str, Any] = {"bufferView": view(arr.tobytes(), target), "componentType": comp, "count": int(len(arr)), "type": kind}
        if minmax:
            acc["min"] = arr.min(axis=0).tolist()
            acc["max"] = arr.max(axis=0).tolist()
        gltf["accessors"].append(acc)
        return len(gltf["accessors"]) - 1

    for el in elements:
        children = []
        for part in el["parts"]:
            pos, nor, idx = flat(part)
            if not len(idx):
                continue
            prim = {
                "attributes": {
                    "POSITION": accessor(pos, "VEC3", 5126, 34962, minmax=True),
                    "NORMAL": accessor(nor, "VEC3", 5126, 34962),
                },
                "indices": accessor(idx, "SCALAR", 5125, 34963),
                "material": material(part.material),
            }
            gltf["meshes"].append({"name": f"{el['name']}:{part.name}", "primitives": [prim]})
            gltf["nodes"].append({"name": part.name, "mesh": len(gltf["meshes"]) - 1})
            children.append(len(gltf["nodes"]) - 1)
        if not children:
            continue
        gltf["nodes"].append({"name": el["name"], "children": children, "extras": el["extras"]})
        gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)

    while len(blob) % 4:
        blob.append(0)
    gltf["buffers"].append({"byteLength": len(blob)})
    if not gltf["materials"]:
        del gltf["materials"]
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    return b"".join([
        struct.pack("<III", 0x46546C67, 2, total),
        struct.pack("<II", len(js), 0x4E4F534A), js,
        struct.pack("<II", len(blob), 0x004E4942), bytes(blob),
    ])


def read_glb_parts(data: bytes) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """A mesh element's GLB → [(part name, vertices in its glTF frame with node transforms applied, faces)]."""
    import trimesh

    scene = trimesh.load(trimesh.util.wrap_as_stream(data), file_type="glb", force="scene")
    out = []
    for node in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[node]
        g = scene.geometry[geom_name]
        if not hasattr(g, "faces") or not len(g.faces):
            continue
        v = trimesh.transform_points(np.asarray(g.vertices, dtype=float), transform)
        out.append((str(node), v, np.asarray(g.faces, dtype=np.int64)))
    return out
