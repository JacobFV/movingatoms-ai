# Saved DirectShape mesh evidence

[Chrome screenshot](directshape.png) of [local technical report](directshape.html). This is not Autodesk UI or an acceptance test. Source run: `research/rvt/local/seed-directshape-run-v3`.

The generator checks the verified RVT SHA-256, all three validation-report hashes against run.json, native/metadata candidate bindings, saved-scene binding, all three record body hashes, owner identity, graph completeness, original-row preservation, mesh totals and normal/winding agreement before rendering. It plots actual saved-scene primitive arrays with feet converted to metres (0.3048); saved normals are dimensionless and remain unchanged. The gray is the reader's initialized default viewport material. No inferred serialized material property or ordinary IFC export is claimed.

Reproduce into a new directory:

```sh
python3 -m venv /tmp/rvt-directshape-capture-venv
uv pip install --python /tmp/rvt-directshape-capture-venv/bin/python --offline matplotlib numpy
/tmp/rvt-directshape-capture-venv/bin/python research/rvt/capture_directshape_evidence.py research/rvt/local/seed-directshape-run-v3 docs/rvt-evidence/2026-10-23-directshape-mesh
```

The destination must not already exist. Chrome 156.0.8078.47 captured the report. After rendering, the screenshot was visually inspected: both views, axes, graph table, evidence boundary and candidate/scene hashes are readable and unclipped. An initial version had crowded X ticks; the final generator uses three X/Y ticks and four Z ticks. The final eight generated artifact hashes, generator hash and four source-report hashes were independently rechecked and passed.

Owner 2746 has complete channels 101/102/103; 36 vertices and 12 triangles are read back. Metadata verifies all 2,300 original element-table rows byte-identical. DirectShape options, lifecycle defaults and unchanged Global/no-registration remain hypotheses. Opening, regeneration and re-saving in Autodesk remain untested; the ordinary public IFC exporter skips DirectShape.

`manifest.json` preserves capture timestamp, Git revision/status, browser/library versions, generator hash, source report hashes and generated-artifact hashes. README is a post-capture review note, so is not part of the capture manifest. The full source reports and metre-converted mesh arrays are archived here; no native model binary is included.
