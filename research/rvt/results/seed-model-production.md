# Offline production-model export control

The actual processing `Model`/geometry code and strict adapter now feed the standalone experimental runtime. The existing synthetic room fixture contains four walls, a door, a window, a slab, a column, a pipe and a beam. The command wrote a saved RVT containing all 10 requested geometry owners, 12 primitives and 312 oriented triangles. All 2,300 seed identities and the source partition remain unchanged.

Candidate SHA256: `47a3e82c61b45d85cde909ffde43d8a53da01c4e403bba2a10d9a81f0232ccf7`.

`seed-model-production.json` binds the original model JSON, runtime bundle manifest, actual request, run report, transport/metadata/native checks and raw saved-scene output. Beyond the independent request check, exact recovered `source_element` records were compared against the original model's live elements. Every owner's `source_context` exactly matches the original level/type arrays and remaining model metadata. Parameters, relationships, transforms if present, absent-vs-null fields and nested properties are retained rather than reconstructed from a lossy mesh.

## Reproduction

Build the compatible-host runtime as described in `docs/rvt-runtime-integration.md`, then use a fresh output directory:

```sh
PYTHONPATH=processing processing/.venv/bin/python -m ma_proc.model.rvt_export \
  research/rvt/results/seed-model-production-input.json \
  --bundle research/rvt/local/runtime-bundle-v1 \
  --output research/rvt/local/seed-model-production-run \
  --runtime-python /usr/bin/python3 \
  --acknowledge-hypotheses
```

The model command requires the processing Python dependencies; the separately launched runtime uses its vendored olefile and prebuilt native binaries. No Revit installation, account, compiler or online service is invoked. `--mesh-directory` can provide hash-verified local GLB assets for mesh-backed elements.

## Qualification

This is a saved-surface export, not a claim of editable native family behavior. Requested level relationships live in our own metadata; native associated-level is unset. Category styles supply the measured preview materials; source material hints survive in metadata but are not claimed as reconstructed Autodesk material assets. Native lifecycle options and category registration remain hypotheses. Autodesk opening, regeneration and re-saving are untested. Customer build jobs remain IFC/GLB; this command produces explicitly experimental artifacts.

Unsupported/missing geometry, unknown categories without explicit adapter policy, ambiguous opening semantics, invalid meshes and over-budget requests fail explicitly. Current profile limits include 100 new native records total, 100,000 input vertices, 200,000 triangles, world coordinates within ±10,000 metres and a bounded finite-JSON metadata envelope. Destinations are no-clobber and verified publication requires all saved-file checks to pass.
