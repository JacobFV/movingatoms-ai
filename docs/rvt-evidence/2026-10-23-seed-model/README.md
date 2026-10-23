# Combined seed-model evidence

[Chrome screenshot](model.png) of the [local technical report](model.html), generated only after the complete frozen pipeline reported `verified_research_candidate` in `research/rvt/local/seed-model-verified-baseline`. This is not Autodesk UI or an Autodesk acceptance test.

Verified candidate SHA-256: `56b5b5274c3f75681e5884d84424fc1678f9f63f308accc317e2c8373a9ca8c5`.

The plot includes all four saved mesh primitives belonging to three new DirectShape owners, totaling 17 triangles: Ground wall (2748), two disconnected Basement open panels Δ (2749), and Roof surface Ω (2750). The vertices and triangles come from independently read-back saved native graphics, never from requested geometry. Feet are converted to metres with 0.3048; normals are archived unchanged. The saved native report verifies all 2,300 original element-table rows remain byte-identical.

Colors use the exact decoded material RGBA: Default Wall and generic default viewport `(0.4980392156862745, 0.4980392156862745, 0.4980392156862745, 1)`; Default Roof `(0, 0.4980392156862745, 0, 1)`. Full material provenance is retained in native.json and mesh-metres.json. These are reader viewport interpretations, not a claim of Autodesk appearance.

Native levels Basement Δ (-3 m), existing Level 1 (0 m) and Roof Ω (7 m) are shown with native and application IDs. The report displays the exact nested application properties, including null, Boolean, numeric and Unicode values. Requested element-level relationships are own extensible-storage metadata; DirectShape native associated-level remains -1. Options, lifecycle and category-registration policies remain hypotheses. Autodesk opening, regeneration and re-saving are untested; ordinary public IFC export skips DirectShape.

Reproduce into a new, absent destination with matplotlib, numpy and Chrome available:

```sh
/tmp/rvt-directshape-capture-venv/bin/python research/rvt/capture_seed_model_evidence.py research/rvt/local/seed-model-verified-baseline docs/rvt-evidence/2026-10-23-seed-model
```

Capture generator source was stable before the complete pipeline run and remained unchanged throughout. `manifest.json` records browser/library versions, timestamp, Git revision/status, generator hash, run/report hashes and eight generated artifact hashes. The generator checks candidate/report/body bindings before rendering. After capture all these hashes were independently rechecked. The screenshot was visually inspected: both views, all named levels, all exact properties, limitations and hash footer are visible and unclipped.

Post-capture review also checks the independently saved raw `candidate-independent-scene.json` hash against native.json, its candidate binding, and exact equality of every plotted primitive and material with its raw owner scene. This raw evidence is archived here; `review.json` records those checks and its hash. README, review.json and this additional raw evidence were added after capture and are therefore outside the capture manifest. No native model binary is included.
