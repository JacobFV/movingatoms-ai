# Named levels and world-metre wall documents

The bounded seed writer now takes a strict metre-based request containing named
levels and walls with application IDs, selected base/top levels, world start
coordinates, lengths, heights and yaw. It retains the seed scaffold and reuses
Level 1 only when explicitly requested under that exact name at zero elevation.
Other requested levels are new native elements; their dependent views are not
cloned from the scaffold. Unsupported thicknesses and intersecting/touching wall
bounds are rejected before writing.

The complete frozen-code workflow passes for Basement Δ at −3 m, Level 1 at
0 m and Roof Ω at 7 m. Walls exercise new→retained, retained→new and new→new
level constraints, with top offsets −0.2, −1 and −2 m. Their independently
triangulated volumes are 2.24, 6 and 4.8 m³, all using the measured 200 mm type.
Native and IFC storey names/elevations agree. All 2,300 original native identities
and the original partition remain preserved.

Candidate SHA: `df86178ad6b6c5a1c277c8dc76dfd2b68fc2c0ab2fbf15dd02b5fc74918e6e21`.

The independent auditor derives geometry and identity mapping directly from the
external request, rather than trusting encoded body graphs. It checks source
level preservation, all new names/plane elevations, native constraints, Global
registrations, complete records, raw metadata, actual meshes and material layers.
The request and complete run/native/metadata/IFC reports are adjacent JSON files.

```sh
python3 research/rvt/seed_document_experiment.py \
  research/rvt/local/minimal_seed-Project.rvt FRESH_OUTPUT \
  --request research/rvt/results/seed-document-request.json \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  --acknowledge-hypotheses
```

The reviewed screenshot is in
`docs/rvt-evidence/2026-10-23-named-levels-corrected/`. The first capture failed
before producing an image because its title code expected the earlier feet-based
report keys; its report copies and explanation are retained separately.
This screenshot is a local evidence report, not Autodesk UI. Native opening,
regeneration, joins, general native families and complete production export are
not established.
