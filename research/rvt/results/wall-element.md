# Schema-encoded straight wall with native geometry

The bounded implementation reconstructs and translates a complete measured
Basic Wall using named schema fields, explicit existing type/level/material
references and a fresh element identity. All three source channel bodies
reproduce exactly; no opaque object-body bytes are copied into the new bodies.
This is a supported straight-wall profile, not arbitrary parametric wall
creation or proof of Autodesk acceptance.

The source is wall **20826** in pinned MIT core2024, Partitions/59. Its native
wall driver disables both end joins and has no opening/join references. The
wall measures approximately **9.5 × 2/3 × 15 feet**. Embedded schema graphs
cover 97 declaration classes and these complete object graphs:

| Channel | Bytes | Objects | Resolved edges |
| --- | ---: | ---: | ---: |
| 101 ElementHeader | 233 | 3 | 2 |
| 102 SWall | 2,946 | 29 | 28 |
| 103 GElement with saved BRep | 6,884 | 74 | 73 |

`wall_element.py` supports the measured scalar types, signed/unsigned integers,
finite float32/float64 values, fixed/counted arrays, nested descriptors,
by-value classes, deferred/shared/external pointers and qualified inherited
fields. It rejects unknown flags, class references, bad array lengths,
nonfinite geometry and ambiguous class identities. Source reconstruction is
checked before any mutation.

The wall uses eight independently verified current context identities:
phase 3, BasicWallType 17328, base Level 20308, top Level 20307, Material 87 and
GStyleElem 113/119/681. Callers must explicitly supply this audited context.
The entry point does not silently substitute another type, level or material.

The supported transform updates exactly 18 named world-coordinate fields:
GLine/Plane origins, header Outline bounds and the root saved GElement bounds.
It leaves direction vectors, local curve parameters, UV coordinates, plane
domains, edge/face topology and empty-cache boxes unchanged. Four explicit
self-identity fields change to fresh ID 133210. Independent re-decode matches
the expected entire graph exactly, including pointer targets.

## Candidate checks

The original control adds a room-bounding wall translated 30 ft X and 20 ft Y.
The outside control translates 400 ft X and 0 ft Y and explicitly sets two
schema-declared booleans false:
`HostObj.m_roomBounding` and
`AnalyticalSpaceBoundingCell.m_isSpaceBounding`.
This optional variant requires acknowledgment of its native lifecycle hypothesis.
Only those two bytes differ from the otherwise identical translated channel 102
body.

[Autodesk's official Rooms guide](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Discipline_Specific_Functionality/Architecture/Revit_API_Revit_API_Developers_Guide_Discipline_Specific_Functionality_Architecture_Rooms_html.html)
identifies `WALL_ATTR_ROOM_BOUNDING` as the parameter controlling room-boundary
participation. The embedded field names and boolean descriptors support the
experiment, but do not prove how Revit updates its caches when that parameter
changes. All 1,219 measured SWall records across the six fixtures had both
booleans true; no source false-control was found. See
[bounding field evidence](wall-element-bounding-flags.json).

The outside candidate's minimum X is 519.5 ft, more than 140.474 ft beyond the
maximum X of every measured current saved header Outline. The bounds audit
fully decodes 26,425 headers and 22,331 finite boxes. It binds all 10 reader
fallback bodies, by SHA-256, to the conservative selector's explicit unique
compaction-history holders; the other 26,415 records have exact episode routes.
No unexplained highest-stream selection is accepted. These are saved bounds,
not proof of evaluated or regenerated geometry. See
[selection-bound bounds audit](wall-element-bounds.json).

For both whole-file candidates, the independent experiment verifies:

- The new wall's complete 106-object/103-edge three-channel graph equals the
  generated model; all positive ElementId references are the fresh self ID or
  the eight explicitly verified context identities.
- Every original source-wall graph remains unchanged.
- Global/Latest preserves 252 objects and 251 edges, with exactly one new ID in
  `StructuralElemSetTracking.m_elemIdSet` and 8 bytes of growth.
- IFC extrusion dimensions, rotation and level remain unchanged, while position
  moves by the requested XY displacement. Material association representation
  differs because the public reader discovers the new wall's line/type route
  where it missed the old one. The candidate integration audit resolves both
  associations to the same actual IFC material; this probe records the differing
  association indices rather than hiding the difference.

Results: [room-bounding control](wall-element.json),
[outside non-bounding control](wall-element-outside.json),
[material route investigation](wall-candidate-material-route.json).
The latter whole-file candidate is
`a9612aa28bcc755fa5536a04aca1a981209bf7119dff65dd4a73c8f7efad02aa`.

## Remaining native lifecycle boundaries

The source wall is referenced by Room 20838's tag anchor, LevelRoomPlan 21258's
circuits/segments and DBView3d 132605's override. Those relationships remain
attached to the retained source wall. They are deliberately not duplicated
onto the new wall. The independent incoming-reference audit records these
references and its decode coverage.

The room-bounding control may require LevelRoomPlan recomputation. The outside
non-bounding variant reduces that particular geometric interaction while
remaining a hypothesis about native lifecycle behavior. It does not establish
that no other creation/regeneration bookkeeping is needed. Geometric history
numbers, topology defaults and flags are re-encoded from measured named values;
their universal creation semantics remain unproven. Nonempty unsigned
partition acceptance also remains unproven.

## Reproduce

```sh
python3 research/rvt/wall_element_experiment.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/wall-target \
  research/rvt/local/core2024.rvt \
  --candidate research/rvt/local/wall-candidate-outside.rvt \
  --translation 400 0 --non-room-bounding \
  --result research/rvt/results/wall-element-outside.json
python3 research/rvt/wall_element_bounds.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/wall-target \
  research/rvt/local/core2024.rvt \
  --result research/rvt/results/wall-element-bounds.json
python3 -m unittest discover -s research/rvt -p 'test_wall_element*.py'
```

Seven payload/registration regression tests pass. The profile is preserved in
[wall-element-profile.json](wall-element-profile.json). All parsing uses file
bytes and the pinned public reader; no proprietary implementation is inspected.
