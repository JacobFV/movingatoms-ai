# Multiple native walls in one save

The research pipeline accepts a JSON list of bounded wall specifications, allocates a
separate native ID for each, and writes them in one new partition and creation episode.
It preserves the pinned source model and performs independent validation before
publishing `verified-candidate.rvt`. That name refers only to the recorded local checks;
it does not mean Autodesk acceptance or a complete production exporter.

## Recorded three-wall result

The complete pipeline passed for [this request](wall-batch-request.json). Candidate
SHA-256: `3f34208b1d94bb99663601aefe1a2054cd3c7e39d695f4abf193401f24967bf6`.
The three new IDs are 133210–133212. Their independently measured saved native volumes
are 60, 120 and 180 ft³. All 26,425 original identities, eight source partitions and
970 projected entities are preserved. All 360 original IFC wall meshes remain exact;
the candidate has 363 walls. Corrected IFC controls have zero schema messages.

Evidence: [run](wall-batch-run.json), [metadata](wall-batch-metadata.json),
[native graphs/solids](wall-batch-native.json), [IFC meshes](wall-batch-ifc.json),
[actual mesh arrays](wall-batch-meshes.json),
[screenshot provenance](../../../docs/rvt-evidence/2026-10-23-wall-batch-corrected/manifest.json).
The integrated Python suite passes 143 tests.

## Reproduce

Use the pinned MIT `core2024.rvt` fixture and the clean pinned public reader documented
in the main research notes. The native transport binary must be built first. IFC checks
require the isolated IfcOpenShell 0.8.5 environment:

```sh
uv venv research/rvt/local/ifc-validation-env
uv pip install --python research/rvt/local/ifc-validation-env/bin/python ifcopenshell==0.8.5
cargo build --release --manifest-path processing/rvt-native/Cargo.toml
uv run --with olefile python research/rvt/wall_batch_experiment.py \
  research/rvt/local/core2024.rvt research/rvt/local/my-wall-batch \
  --specs research/rvt/results/wall-batch-request.json \
  --reader-source /path/to/pinned/rvt-rs \
  --acknowledge-hypotheses
```

The output directory must be new. The request uses feet:

```json
[
  {"length_feet": 6.0, "translation_xy": [400.0, 0.0]},
  {"length_feet": 12.0, "translation_xy": [430.0, 0.0]},
  {"length_feet": 18.0, "translation_xy": [470.0, 0.0]}
]
```

Each wall retains the measured width, height, type, levels and planar geometry profile.
The request must contain 1–100 unique specifications. The builder rejects nonfinite
values, unsupported lengths, touching/overlapping new bounds, and placements within
the source model's measured saved bounds. These spatial restrictions reduce known
interactions; they do not establish native regeneration semantics.

## Validation and publication

The builder validates the whole request and constructs all logical payloads before
creating its patch directory. It updates all new table rows and self references,
registered ID sets, partition object sequences, History, both increment arrays,
BasicFileInfo, Contents and measured ancillary metadata. Both element-count fields
in the new increment are set to the batch size; the earlier single-object constant
would have been wrong for this transaction.

The independent metadata auditor reads source and candidate bytes to check sequential
IDs, a shared creation episode, old row/episode/partition preservation, registration
union, all channel records, counters and identity copies. A separately compiled pinned
public reader then decodes every new graph. The native BRep audit reconstructs face
loops and measures closed-solid geometry without relying on wall parameters or IFC.
IfcOpenShell/OpenCASCADE checks the actual exported meshes, preserving all existing
wall meshes and measuring each new wall's bounds, volume and material.

The IFC exporter has a pre-existing OwnerHistory schema issue. Separate correction
controls modify only LastModifiedDate from CreationDate; all other entity attributes
are preserved. The pipeline requires zero schema errors in those explicit controls.
It does not silently modify the RVT to resolve an IFC-only issue.

Only after every subprocess passes, report hashes bind the same candidate, and code,
source and writer hashes remain stable does the runner publish its native artifact.
Publication refuses to overwrite an existing file. Failed runs retain staging files
and logs with `status: failed` in `run.json`, and do not publish a verified artifact.

## Remaining boundary

This is still a pinned-source, straight-wall research workflow. It does not support
arbitrary documents, new types, joins, openings or complete model-to-RVT export.
Foreign-producer framing, native regeneration, preview updating and Autodesk
acceptance remain unverified. The runner never labels these claims as established.
