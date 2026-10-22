"""Scan points for fits and heatmaps.

A scan's viewer layer is a Potree 2.0 octree (metadata.json, hierarchy.bin, octree.bin). With the DEFAULT encoding,
octree.bin is every node's points back to back, uncompressed, one fixed-size record per point; a point's index in the
layer is its byte offset / bytes per point. That's the order heatmap attribute pages follow (the vendored Potree reads
a node's span at byteOffset / attributes.byteSize). BROTLI-encoded layers can't be indexed that way: ingest must write
DEFAULT. When a scan has no layer yet, the intermediate LAS ingest leaves at
projects/<pid>/scans/<scan_id>/labelled.las is read instead (order doesn't matter for fits).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

# Potree 2.0 attribute types → numpy dtypes
_TYPES = {
    "int8": "<i1", "uint8": "<u1", "int16": "<i2", "uint16": "<u2", "int32": "<i4", "uint32": "<u4",
    "int64": "<i8", "uint64": "<u8", "float": "<f4", "double": "<f8",
}


@dataclass
class Layer:
    """A scan layer's points in octree order."""
    xyz: np.ndarray  # (N, 3) float64, working frame
    classification: np.ndarray | None  # (N,) uint8, the ma-v1 labels when the layer has them
    metadata_key: str  # projects/<pid>/…/metadata.json
    bytes_per_point: int
    points: int


def bytes_per_point(metadata: dict) -> int:
    return int(sum(int(a["size"]) for a in metadata["attributes"]))


def decode_octree(metadata: dict, octree: bytes | np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """octree.bin (DEFAULT encoding) → (xyz in octree order, classification or None)."""
    enc = str(metadata.get("encoding", "DEFAULT")).upper()
    if enc != "DEFAULT":
        raise ValueError(f"the scan layer is {enc}-encoded; heatmaps and fits need DEFAULT (uncompressed) layers")
    bpp = bytes_per_point(metadata)
    raw = np.frombuffer(octree, dtype=np.uint8) if not isinstance(octree, np.ndarray) else octree
    n = len(raw) // bpp
    rec = raw[: n * bpp].reshape(n, bpp)
    offset = 0
    xyz = None
    cls = None
    scale = np.asarray(metadata.get("scale", [1, 1, 1]), dtype=np.float64)
    origin = np.asarray(metadata.get("offset", [0, 0, 0]), dtype=np.float64)
    for a in metadata["attributes"]:
        size = int(a["size"])
        name = a["name"]
        if name in ("position", "POSITION_CARTESIAN"):
            ints = np.ascontiguousarray(rec[:, offset : offset + 12]).view("<i4").reshape(n, 3)
            xyz = ints.astype(np.float64) * scale + origin
        elif name == "classification":
            dt = _TYPES.get(a.get("type", "uint8"), "<u1")
            cls = np.ascontiguousarray(rec[:, offset : offset + size]).view(dt).reshape(n, -1)[:, 0].astype(np.uint8)
        offset += size
    if xyz is None:
        raise ValueError("the scan layer has no position attribute")
    return xyz, cls


def scan_layer_prefix(scan: dict) -> str | None:
    """The scan's full layer's key prefix (projects/<pid>/…), or the overview layer, or the legacy single octree."""
    viewer = scan.get("viewer") or {}
    for layer in (viewer.get("full"), viewer.get("overview")):
        if isinstance(layer, dict) and layer.get("potree_prefix"):
            return str(layer["potree_prefix"]).rstrip("/")
    return str(scan["potree_prefix"]).rstrip("/") if scan.get("potree_prefix") else None


def _abs_key(pid: str, key: str) -> str:
    return key if key.startswith("projects/") else f"projects/{pid}/{key.lstrip('/')}"


def load_layer(api: Any, pid: str, scan: dict, workdir: Path) -> Layer | None:
    prefix = scan_layer_prefix(scan)
    if not prefix:
        return None
    prefix = _abs_key(pid, prefix)
    workdir.mkdir(parents=True, exist_ok=True)
    meta_path = api.download(f"{prefix}/metadata.json", workdir / f"{scan['id']}-metadata.json")
    metadata = json.loads(meta_path.read_text())
    oct_path = api.download(f"{prefix}/octree.bin", workdir / f"{scan['id']}-octree.bin")
    octree = np.memmap(oct_path, dtype=np.uint8, mode="r")
    xyz, cls = decode_octree(metadata, octree)
    return Layer(xyz, cls, f"{prefix}/metadata.json", bytes_per_point(metadata), int(metadata.get("points", len(xyz))))


def load_points(api: Any, pid: str, scan: dict, workdir: Path) -> np.ndarray | None:
    """A scan's points (any order): its viewer layer, else ingest's labelled.las."""
    try:
        layer = load_layer(api, pid, scan, workdir)
        if layer is not None:
            return layer.xyz
    except Exception:  # noqa: BLE001 - fall back to the LAS
        pass
    import laspy

    for ext in ("laz", "las"):  # ingest stores LAZ now; scans ingested earlier have LAS
        key = f"projects/{pid}/scans/{scan['id']}/labelled.{ext}"
        if api.exists(key):
            break
    else:
        return None
    path = api.download(key, workdir / f"{scan['id']}-labelled.{ext}")
    las = laspy.read(path)
    return np.stack([np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)], axis=1).astype(np.float64)


def ready_scans(scans: list[dict], scan_id: str | None = None) -> list[dict]:
    return [s for s in scans if s.get("status") == "ready" and (scan_id is None or s.get("id") == scan_id)]
