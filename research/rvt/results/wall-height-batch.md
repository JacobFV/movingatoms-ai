# Coordinated height, length and yaw save

The full writer → metadata audit → independent native decode/BRep → IFC kernel
workflow passes for three walls: 6×8 ft at45°,12×10 ft at90°,18×20 ft at−30°.
Native volumes are32,80,240ft³. The existing360wall meshes and26,425native
identities remain unchanged. Corrected IFC controls have zero schema errors.

Candidate SHA-256: `0821a30548273a3f2d19b998f8fc45febc48ca12ca96c94143a45fe056931180`.

Height changes update the measured top offset and cached height scalar alongside
plane/UV geometry; base/top level IDs and inactive unconnected-height value remain
unchanged. The independent verifier checks these constraints, vertices, volume,
surface area and saved bounds. Default15ft output stays byte-identical.
The combined research suite passes167tests at this checkpoint.

Full reports are in `wall-height-batch-{run,metadata,native,ifc,meshes,plan,request}.json`.
The run hashes stable code before/after execution. Actual IFC mesh plots and a
reviewed Chrome screenshot are in `docs/rvt-evidence/2026-10-23-wall-heights/`.
These remain pinned-source research candidates; Autodesk opening/regeneration is
not tested and production native output remains disabled.

```sh
python3 research/rvt/wall_batch_experiment.py research/rvt/local/core2024.rvt FRESH_OUTPUT \
  --specs research/rvt/results/wall-height-batch-request.json \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --acknowledge-hypotheses
```
