# Minimal native document: verified research run

The single-command seed workflow creates one upper level and three new walls
without retaining a donor building. The source is the pinned MIT Revit 2024
project; its 2,300 scaffold identities and original partition remain unchanged.
Only the requested three physical elements appear in the independent projection.

Candidate SHA-256: `559b7b45e0f05ae724352c41f550a6c1528e63b6272ba10f74de1c0478b2506d`.

| Native ID | Length × height | Yaw | Independent IFC volume |
| --- | --- | --- | --- |
| 2747 | 6 × 8 ft | 45° | 0.891869184 m³ |
| 2748 | 12 × 10 ft | 90° | 2.229672960 m³ |
| 2749 | 18 × 20 ft | −30° | 6.689018880 m³ |

All walls use the seed's existing 200 mm single-layer type, materials and styles,
with geometry near the origin at Z0. Level 2746 is added at 15 ft. Wall top
offsets reflect their individual heights; base level 1916 remains at zero.

## Independent checks

The orchestrator writes to staging and publishes `verified-candidate.rvt` only
after transport, metadata, native and IFC checks pass and bind the exact same
candidate SHA. Source code, source file, writer and input profiles are hashed
before and after execution. Failure retains logs and never publishes a verified
artifact. Here, verified means the recorded local research checks only.

The metadata audit derives four new IDs and both increment-array counts from
actual file bytes. It checks old rows, History episodes, Contents revision spans
and its measured zero suffix, four BasicFileInfo identity copies, XML timestamps
with the measured 10,800-second offset, and unchanged unrelated streams.

The native audit independently decodes actual saved records and retained context.
It verifies exact current routes, complete bodies, all positive references,
requested BRep vertices, bounds, areas and volumes, type width and level offsets.
The decoded Global graph changes only the three intended registration lists.

IfcOpenShell/OpenCASCADE checks the actual projected meshes against a strict
serialization oracle. Materials, 200 mm layer thickness, orientation and offset
are checked against the seed. Raw IFC retains the public exporter's known
OwnerHistory issue; explicit correction controls have zero schema findings.
The combined research suite passes **212 tests** at this checkpoint.

Full reports: `seed-wall-{run,metadata,native,ifc,plan,request}.json`. Actual mesh
arrays are in the IFC report. A visually reviewed Chrome screenshot and exact
input report copies are in `docs/rvt-evidence/2026-10-23-seed-walls/`.

## Reproduce

```sh
python3 research/rvt/seed_wall_experiment.py \
  research/rvt/local/minimal_seed-Project.rvt FRESH_OUTPUT \
  --specs research/rvt/results/seed-wall-request.json \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  --acknowledge-hypotheses
```

This remains a bounded research writer: nonintersecting, non-room-bounding,
straight rectangular walls using one measured type and fixed level context.
Arbitrary meshes, full application metadata and general model export remain
separate implementation work. Native opening, regeneration and re-saving have
not been tested. Producer-field and creation-lifecycle policies remain hypotheses.
No production native-output claim is made.
