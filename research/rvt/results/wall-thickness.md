# Coherent wall thickness for an existing target type

`wall_thickness.py` changes the measured wall's transverse geometry before height, length and yaw. The intended target is the seed document's existing 200mm single-layer type, not a modification of that type. A nondefault width requires explicit acknowledgment that the caller must subsequently validate/remap the wall to an existing type with that width. The seed context adapter performs that separate validation.

The source wall has thickness 2/3 foot. Its driver follows the middle of the solid; the transverse affine transform scales distances from that driver. It changes world plane origins, each plane's transverse UV distances, corresponding loop envelopes and edge endpoints, solid-fill UV origins, and saved bounding boxes. Unit directions, curve parameters, longitudinal dimensions and topology remain unchanged. All four channel-102 reference planes and four channel-103 reference sheets participate in the same transform.

The serialized key-reference offset also changes from 1/3 foot to half the requested width. This is supported by 209 existing unflipped walls with the same `m_wallKeyRef=2` convention and four independently decoded single-layer types: widths 2/3, 1/2, 1/2 and 3/2 feet. Each observed key offset equals half its type width within 1e-12 foot; location-line offsets are zero. The encoder rejects other key-reference/flip/offset states. This is measured file evidence, not an assumed mapping of the internal enumeration to a public API enumeration.

Four focused tests pass. Default width reconstructs the source profile and entire existing height encoder result exactly. Widths 200mm, 1/2 foot and 3/2 feet pass independent native BRep area/volume and transverse-width checks after height 20, length 12 and yaw 45. Nine encoded channel bodies independently decode to the exact intended graphs. All 24 paired edge endpoints agree. [The evidence report](wall-thickness.json) includes type-body hashes, the 209 wall checks, generated body hashes and geometry measurements.

```sh
python3 -m unittest discover -s research/rvt -p test_wall_thickness.py
python3 research/rvt/wall_thickness_experiment.py research/rvt/local/core2024.rvt \
  --probe research/rvt/local/new-element-build/target/release/rvt-wall-element-probe \
  --schema research/rvt/local/core2024.schema \
  --result research/rvt/results/wall-thickness.json
```

The supported input remains the measured centered rectangular source profile. Width must be finite and between 0.01 and 10 feet. The helper does not change a wall type's compound structure, material definition or layer metadata. Before saving a changed-width wall, the caller must match its geometry to the actual target type and context; the helper alone deliberately reports that requirement as outstanding. Native regeneration and Autodesk acceptance remain untested.
