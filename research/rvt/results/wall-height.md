# Height with retained native level constraints

The bounded encoder changes height while retaining the source wall's base and top level identities. It coordinates the level offset parameters and the cached native BRep; it does not merely scale the exported geometry.

Independent decoding of the pinned source identifies base Level 6 (20308) at Z=76 feet and top Level 7 (20307) at Z=91 feet. Each level has two matching horizontal plane records. The [Autodesk public parameter enumeration](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/fb011c91-be7e-f737-28c7-3f1e1917a0e0.htm) identifies -1001109 as Top Offset, -1001108 as Base Offset, and -1001105 as Unconnected Height.

The original wall has zero top/base offsets and an actual height of 15 feet, but its stored Unconnected Height is 8 feet. Consequently the implementation preserves that inactive value. It changes Top Offset to `requested height - 15` while keeping both level references and Base Offset unchanged.

A second serialized scalar, -1001101, equals actual height in the measured examples. It has no entry in the current public parameter enumeration, so its interpretation is empirical. Two actual walls sharing these same levels provide nonzero-offset controls:

| Source wall | Top offset (feet) | Saved geometry height (feet) | Scalar -1001101 |
| --- | ---: | ---: | ---: |
| 20826 | 0 | 15 | 15 |
| 20807 | 5.172120412901791 | 20.17212041290179 | 20.17212041290179 |
| 20897 | -0.6666666666666666 | 14.333333333333329 | 14.333333333333329 |

The encoder sets that scalar to requested height, consistent with all three controls. Source hashes, level identities, record locations, parameter values and saved boxes are recorded in [wall-height.json](wall-height.json). This evidence establishes a measured relationship, not the complete native parameter evaluation lifecycle.

`wall_height.py` stretches world Z about the unchanged base elevation and scales only each plane's vertical UV coordinate. It updates plane/loop envelopes, edge UV endpoints, solid-fill UV origins, reference planes and the three saved bounding boxes. Plane directions, horizontal line parameters, topology, level IDs and type thickness stay unchanged. It then delegates length and yaw to the existing encoders. The supported source requires its exact measured parameter set and level pair; changed extensions, base offsets, level IDs, slanted frames and other unmeasured states are rejected.

Four focused tests pass. Nominal height 15 preserves the entire previous encoder result exactly. Heights 8, 10, 20 and 25 feet, combined with length 12 feet and yaw 45 degrees, pass native closed-solid volume/bounds checks. The public reader independently decodes all twelve generated channel bodies to the exact intended graphs. The 24 paired face endpoints agree after each change. These are body-level tests; saved whole-file verification and Autodesk acceptance are separate.

```sh
python3 -m unittest discover -s research/rvt -p test_wall_height.py
python3 research/rvt/wall_height_experiment.py research/rvt/local/core2024.rvt \
  --probe research/rvt/local/new-element-build/target/release/rvt-wall-element-probe \
  --schema research/rvt/local/core2024.schema \
  --result research/rvt/results/wall-height.json
```

The implementation remains a pinned-fixture experiment with the existing unsigned-save and non-room-bounding hypotheses. It does not claim general wall authoring or native regeneration acceptance.

## Batch integration

The batch builder now accepts optional `height_feet`. Missing or nominal15 values normalize away, preserving the old request and deterministic episode GUID. A fresh nominal-height generation matched every legacy patch, manifest and plan byte for byte. The shared verifier independently checks decoded native level IDs, base/top offsets, inactive unconnected height, the measured cached-height scalar, requested solid vertices/volume/area and IFC projection height. It rejects wrong-height IFC projections and tampered native constraints. All25 batch-related focused tests plus4 height tests pass at this checkpoint. Whole-file height pipeline results are recorded separately by the orchestrator.
