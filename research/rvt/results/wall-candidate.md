# Translated native wall candidate controls

These are clean-room file-byte experiments, not Autodesk-accepted saves or a production native exporter. Source is the pinned MIT core2024 fixture (`c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014`). The independent public reader remains pinned at `b6086d41b9758fd9b92f42f0a47b8345b9c58056` with clean source checks.

## Latest outside/non-room-bounding experiment

`local/wall-candidate-outside.rvt` SHA-256: `a9612aa28bcc755fa5536a04aca1a981209bf7119dff65dd4a73c8f7efad02aa`.

Wall 20826 supplies a fully decoded schema profile. The encoder constructs fresh bodies for ID 133210, translates world coordinates +400 feet X, and explicitly sets both measured room/space-bounding booleans false. That boolean lifecycle is a hypothesis: no native false-source wall was observed. Original partitions and all 26,425 native identities are retained, and the fresh creation episode produces UniqueId `859411ca-d713-532e-a032-d1ac0f41975a-0002085a`.

The guarded writer creates Partitions/66, advances History/element table/increments, synchronizes Contents/BasicFileInfo, applies the measured ancillary revision/timestamp policy, and inserts the ID in StructuralElemSetTracking. The actual candidate's Global/Latest is independently decoded and compared, allowing only the new registration. All three new native graphs decode completely and match the schema encoder: 3/29/74 objects in channels 101/102/103.

The public IFC exporter adds one wall while preserving every prior BuildingElement entity and native IFC identity. IfcOpenShell 0.8.5/OpenCASCADE reads the emitted STEP files: all 360 old wall meshes are exactly preserved; wall 361 has 8 vertices/12 triangles and the expected +121.92 metre X translation. The shape is 9.5 × 2/3 × 15 feet, approximately 2.69010042624 cubic metres. Coordinate and volume comparisons use absolute tolerances of 1e-8 metres and 1e-8 cubic metres; the native exporter floating comparisons use 1e-10 feet.

Material representation differs: old wall directly associates IFC material #111 `Default Wall`; the new wall uses a one-layer set referencing that same material, with thickness 0.2032 metres matching the mesh. The public historical scanner has no unambiguous line for the original ID but finds one for the fresh ID, allowing extra layer information. This is a representational difference, not evidence of changed physical material. `wall-candidate-material-route.json` records the lookup and its remaining diagnostic limit.

Both unmodified IFC exports have the same pre-existing IFC OwnerHistory EXPRESS-rule error: `.ADDED.` with no LastModifiedDate. Separate explicitly named correction controls use IfcOpenShell's semantic API to set that one attribute from CreationDate. The serialized controls preserve every other entity/attribute, pass the schema validator with zero messages, and pass the mesh comparisons. Original exports and RVT files are untouched. This correction does not establish RVT acceptance.

## Preserved earlier control

`local/wall-candidate.rvt` translates +30 feet X/+20 feet Y and retains source bounding behavior. It remains a control with unresolved room-topology consequences. Its independent native and IFC evidence is retained separately in `wall-candidate-{verification,ifc,ifc-owner-control}.json`.

## Reproduction

Run from repository root, with the pinned fixture/profile/registration evidence present:

```sh
python3 research/rvt/wall_candidate.py research/rvt/local/core2024.rvt research/rvt/local/wall-candidate-outside --registration-evidence research/rvt/results/wall-element-registration.json --acknowledge-hypotheses --translation 400 0 --non-room-bounding
processing/rvt-native/target/release/ma-rvt-native patch research/rvt/local/core2024.rvt research/rvt/local/wall-candidate-outside.rvt research/rvt/local/wall-candidate-outside/manifest.json
python3 research/rvt/wall_candidate_verify.py --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --target /tmp/rvt-wall-candidate-target research/rvt/local/core2024.rvt research/rvt/local/wall-candidate-outside.rvt --translation 400 0 --non-room-bounding
uv venv research/rvt/local/ifc-validation-env
uv pip install --python research/rvt/local/ifc-validation-env/bin/python ifcopenshell==0.8.5 pytest==8.4.2
research/rvt/local/ifc-validation-env/bin/python research/rvt/wall_candidate_ifc.py research/rvt/local/wall-candidate-outside-source.ifc research/rvt/local/wall-candidate-outside-candidate.ifc --new-guid 25b17ArnDJBg0oqQmFGvy0 --translation 400 0
research/rvt/local/ifc-validation-env/bin/python research/rvt/wall_candidate_ifc_owner_control.py research/rvt/local/wall-candidate-outside-source.ifc research/rvt/local/wall-candidate-outside-candidate.ifc --new-guid 25b17ArnDJBg0oqQmFGvy0 --translation 400 0
```

The builder/writer require fresh output paths. The verifier permits an existing IFC artifact only if its bytes match. Reports bind source/candidate hashes, tool versions and relevant tool hashes. `wall-geometry-evidence.json` contains small genuine world-coordinate IFC meshes for documentation screenshots; it is not a Revit UI capture.

Open issues remain: unsigned partition enforcement, full native save policy, regeneration/cache lifecycle, preview updates, unmeasured incoming registration rules and Autodesk acceptance. Moving outside measured source bounds and setting measured booleans false narrows this experiment; it does not prove those lifecycle rules.
