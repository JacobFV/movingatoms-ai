# Offline production-model evidence

[Chrome screenshot](model.png) of the [local technical report](model.html), captured from the fully verified offline production CLI run `research/rvt/local/seed-model-production-run`.

Candidate SHA-256: `47a3e82c61b45d85cde909ffde43d8a53da01c4e403bba2a10d9a81f0232ccf7`.

The saved scene has ten DirectShape owners, twelve mesh primitives and 312 triangles: four walls, door, window, slab, column, pipe and beam representations. Both views use actual independently read-back native graphics, including openings and interior components. All source-style viewport colors and opacity are used exactly as decoded; no request geometry is used to draw the scene. Feet are converted to metres with 0.3048, and normals remain unchanged in the archived arrays.

The property table summarizes each recovered source element's props/params/transform where present and source-context counts. Full envelopes, including representation metadata and context, remain in native.json and the independently saved raw scene. The native verifier reports exact application-property recovery for every owner. This is recovery through our own extensible-storage schema, not proof of native Revit parametric behavior. Ground is a new named native level; element-to-level relationships remain application metadata, with native associated-level unset (-1).

The generator verifies candidate, run, validation-report and channel-body hash bindings. It also verifies the independent raw scene hash and exact equality of every plotted primitive/material with that raw scene. All nine generated artifact hashes, five source-report hashes and generator hash were independently rechecked after capture. Final screenshot visually inspected: both views, all ten summary rows, named level, limitations and hash footer are readable and unclipped. Chrome version, timestamp, Git revision/status and library versions are recorded in manifest.json.

Reproduce into an absent directory:

```sh
/tmp/rvt-directshape-capture-venv/bin/python research/rvt/capture_production_model_evidence.py research/rvt/local/seed-model-production-run docs/rvt-evidence/2026-10-23-production-model
```

This is a genuine Chrome capture of a generated technical report, not Autodesk UI. Lifecycle/options/category-registration policies remain hypotheses; Autodesk opening, regeneration and re-saving remain untested. Ordinary public IFC export skips DirectShape. “Production model” identifies the input adapter/CLI execution path, not certification of native application acceptance.

This README is a post-capture review note outside manifest.json. No native model binary is included.
