# Bounded native wall length encoder

The schema-driven encoder changes the measured straight wall from 9.5 to 12 feet while retaining its 2/3-foot type thickness, 15-foot height, existing type, levels, phase and material identities. The saved candidate independently decodes to all three intended native object graphs; its original wall is unchanged. This is a fixture-bound research writer, not evidence of Revit acceptance.

## Construction and checks

`wall_parametric.py` applies a longitudinal affine transform anchored at the original wall axis start. It changes named world positions, the axis parameter interval, each plane's longitudinal UV coordinate, face and loop UV envelopes, edge endpoints, fill-placement origins, and saved bounding boxes. Unit directions and topology remain unchanged. Each edge's two UV representations use their own adjacent plane basis. The axis starts at parameter -0.25, so scaling its origin and parameter interval together is necessary to preserve the actual start point.

The nominal 9.5-foot request reconstructs all three source bodies byte for byte. The 12-foot request changes 54 named geometry fields. All 24 paired edge endpoints agree in world coordinates within 1.43e-14 feet after the length change and translation. The final bounds are approximately `[519.5, 67.4166667, 76]` to `[531.5, 68.0833333, 91]` feet.

The independent verifier rebuilds the pinned public reader, binds the original source record hashes, and decodes the actual saved candidate rather than an in-memory encoding. All three graphs and body hashes match; see [machine-readable evidence](wall-parametric.json). Candidate SHA-256: `271c54903276ebc540206979d8b54d008aec485fb823704433633f909de54c39`.

Independent validation of the saved native BRep found a closed solid with six faces, twelve edges, eight vertices, opposite directed edge incidence, Euler characteristic two, volume 120 cubic feet, and surface area 396 square feet. Its vertex bounds match both saved root boxes. Four open reference sheets are excluded from volume. This verifier does not use the SWall axis or IFC; see [native BRep evidence](wall-brep-audit.json). The separate [whole-file candidate report](wall-parametric-candidate.md) records IFC/OpenCascade checks and preservation of the existing geometry.

## Explicit supported profile

The encoder requires the measured three-channel graph shape, one horizontal world-axis-aligned line, planar faces with orthogonal aligned UV bases, straight edges, unpatterned fills, and the two measured empty channel-102 cache sentinels. It rejects nonempty caches, extra lines, curved edges, oblique plane bases, nonfinite geometry, and missing paired endpoints. Length must be finite and between 0.01 and 10,000 feet. Height, thickness, arbitrary orientations, joins, openings, and arbitrary document profiles are unsupported.

The candidate retains the outside-model translation and explicitly acknowledged non-room-bounding flag hypothesis of the translated-wall experiment. Native lifecycle, room/topology cache behavior and acceptance by Autodesk software remain unvalidated. A coherent closed BRep and successful independent decoding do not establish those properties.

## Reproduction

```sh
python3 -m unittest discover -s research/rvt -p test_wall_parametric.py
python3 research/rvt/wall_parametric_verify.py \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  --target research/rvt/local/new-element-build/target \
  research/rvt/local/core2024.rvt \
  research/rvt/local/wall-parametric-candidate.rvt \
  --result research/rvt/results/wall-parametric.json
```

Eight focused tests pass, including exact nominal reconstruction, several changed lengths, preserved dimensions and direction fields, corrupted-edge rejection, unsupported-cache rejection, and finite-value guards.
