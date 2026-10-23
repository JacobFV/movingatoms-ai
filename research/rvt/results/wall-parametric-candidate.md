# Twelve-foot native wall candidate

The fresh outside/non-room-bounding wall experiment now includes a bounded length change from 9.5 to 12 feet. The encoder anchors the original wall's start and transforms world geometry plus the corresponding face-local UV coordinates. The new wall remains translated +400 feet X. This is experimental native file authoring; signatures, regeneration lifecycle and Autodesk acceptance remain unresolved.

Candidate `local/wall-parametric-candidate.rvt` SHA-256:
`271c54903276ebc540206979d8b54d008aec485fb823704433633f909de54c39`.

Every stream except Partitions/66 is byte-identical to the independently verified outside control (`a9612aa28bcc755fa5536a04aca1a981209bf7119dff65dd4a73c8f7efad02aa`). This binds the previous 26,425 native identities and measured registration to the unchanged save metadata. A separate clean pinned-reader invocation independently decodes all three new graphs and compares them against the coherent parametric encoder. All 970 existing projected BuildingElement entities and native IFC IDs remain unchanged.

The emitted STEP file is independently triangulated by IfcOpenShell 0.8.5/OpenCASCADE. All 360 pre-existing wall meshes remain exactly equal. The new wall's world bounds are `[158.3436, 20.5486, 23.1648]` to `[162.0012, 20.7518, 27.7368]` metres: 12 × 2/3 × 15 feet, with 8 vertices and 12 triangles. Its measured volume is 3.39802159104147 cubic metres versus expected 3.39802159104000. Absolute tolerances are 1e-8 metres and 1e-8 cubic metres. The Default Wall layer remains 0.2032 metres thick.

The raw IFC exports retain the same pre-existing OwnerHistory rule violation. Separate explicit correction controls set only LastModifiedDate from CreationDate, preserving every other entity attribute. Corrected source and candidate validate with zero schema messages and pass the same geometry checks. No native RVT bytes are changed by this IFC-only correction.

**Validation boundary:** the IFC exporter may derive its extrusion from wall driver geometry. These checks validate the actual emitted IFC shape; they do not independently prove physical consistency of the native BRep. The saved native BRep audit is separate. Graph decode/encoder equality likewise does not establish native regeneration or application acceptance.

## Reproduction

```sh
python3 research/rvt/wall_parametric_candidate.py research/rvt/local/core2024.rvt research/rvt/local/wall-parametric-candidate --acknowledge-hypotheses
processing/rvt-native/target/release/ma-rvt-native patch research/rvt/local/core2024.rvt research/rvt/local/wall-parametric-candidate.rvt research/rvt/local/wall-parametric-candidate/manifest.json
python3 research/rvt/wall_parametric_candidate_verify.py --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --target /tmp/rvt-wall-candidate-target research/rvt/local/wall-candidate-outside.rvt research/rvt/local/wall-parametric-candidate.rvt
research/rvt/local/ifc-validation-env/bin/python research/rvt/wall_parametric_candidate_ifc.py research/rvt/local/wall-candidate-outside-source.ifc research/rvt/local/wall-parametric-candidate.ifc --correct-owner-history
```

Use fresh builder/writer destinations. The same isolated IfcOpenShell environment used for the translated-wall controls applies. Reports are `wall-parametric-candidate-{plan,writer,verification,ifc,ifc-owner-control}.json`; actual small mesh screenshot input is `wall-parametric-candidate-geometry.json`. Three focused dimension/volume/nonfinite guards pass.
