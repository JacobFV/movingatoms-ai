# Rigid yaw of the measured native wall

`wall_oriented.py` applies a proper XY rotation after length stretch and before placement translation. Its pivot is the original wall axis start, approximately `[119.5, 67.75, 76]` feet. This order retains the existing axis-aligned length encoder while allowing the resulting wall to face a different direction.

The transform updates the channel-102 line's origin and unit direction, plus all fourteen plane origins and both basis vectors: four channel-102 reference planes and ten channel-103 solid/reference planes. It reconstructs the header Outline and both root geometry bounds from the eight actual solid vertices. It preserves face UV coordinates, edge UVs, plane/loop UV envelopes, line end parameters, filling placement UVs, local wall offsets, topology and parity flags. The two empty channel-102 geometry caches remain empty.

The batch request accepts optional `yaw_degrees` between -360 and 360. A missing or zero value normalizes to the original request shape. A fresh generated zero-yaw batch was compared against the previous checkpoint: every patch file, manifest, plan and episode GUID is byte-identical. This is recorded in [the measurement report](wall-oriented.json).

Ten focused tests pass across the oriented encoder and batch builder. Rotation tests at 45, 90, -30, 180 and 360 degrees compare every actual native solid vertex with an independently computed rigid transform. They verify 24 paired edge endpoints, preserved UV/topology fields, valid native BRep bounds, volume 120 cubic feet and surface area 396 square feet for the 12-foot wall. Invalid angles and nonorthonormal frames are rejected. The separate native BRep auditor measures geometry from face loops rather than the wall driver.

These measurements validate encoder output graphs; independently decoding the saved whole-file candidate and comparing IFC geometry are separate stages. Proper rotation does not justify changes to flip/mirror flags, but their native lifecycle semantics and Autodesk acceptance remain unproven. Support remains limited to the measured straight, planar, unjoined wall with its existing context and acknowledged non-room-bounding hypothesis.

```sh
python3 -m unittest discover -s research/rvt -p test_wall_oriented.py
python3 -m unittest discover -s research/rvt -p test_wall_batch_candidate.py
```

A three-wall yaw request can use lengths 6, 12 and 18 feet; translations `[400,0]`, `[430,20]`, `[470,0]`; and yaw angles 45, 90 and -30 degrees, respectively. All resulting saved AABBs remain disjoint and east of the measured source bounds.


## Saved-file and IFC integration result

The complete runner passes for [the three-angle request](wall-oriented-request.json).
Candidate SHA-256: `9a8f89c26c6e530d802ddd918612a18948b366446b6a0940478a6c3464086556`.
All new graphs decode completely; native closed solids measure 60/120/180 ft³ and
match independently calculated rigid transforms. All 26,425 original native identities,
eight source partitions, 970 projected entities and 360 prior IFC wall meshes are
preserved. Both explicit OwnerHistory correction controls have zero schema messages.
The full integrated Python suite passes **154 tests**.

The first run failed because the verifier required one particular IFC parameterization.
The 90° wall is physically equivalent when local width/depth swap and the placement
frame becomes unrotated. The corrected checker validates all eight physical vertices,
placement, surface area, volume, and material thickness axis/direction/offset. Swapping
dimensions without a matching basis is still rejected. The failed and successful runs
bind **identical RVT bytes**; no geometry workaround or IFC correction adapter was needed.
The failure also exercises the runner's publication guard: no verified artifact appeared.

The pinned public STEP writer emits placement coordinates and direction vectors to six
decimal places (`src/ifc/step_writer.rs`, lines 2076/2087 at the pinned revision). The
verifier independently validates the equivalent unrounded frame first, constructs its
six-decimal serialization, normalizes that direction as IFC does, and checks actual
triangulated vertices within 1e-8 m of that precise serialized geometry. Native vertices
remain checked against ideal requested geometry within 1e-7 ft. Maximum measured IFC
vertex deviation from ideal geometry is 0.624 micrometres, within the explicitly derived
rounding bound. These are separate measurements, not a blanket tolerance increase.

Reports: [run](wall-oriented-run.json), [metadata](wall-oriented-metadata.json),
[native](wall-oriented-native.json), [IFC and quantization](wall-oriented-ifc.json),
[mesh arrays](wall-oriented-meshes.json), [initial failed run](wall-oriented-failed-run.json).
[Actual mesh screenshot and provenance](../../../docs/rvt-evidence/2026-10-23-oriented-walls/manifest.json).
Use the batch runner recipe with `--specs research/rvt/results/wall-oriented-request.json`.
