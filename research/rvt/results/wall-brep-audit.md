# Saved native wall BRep verification

The actual parametric RVT candidate, SHA-256
`271c54903276ebc540206979d8b54d008aec485fb823704433633f909de54c39`,
contains a closed native planar solid measuring **120 cubic feet** with
**396 square feet** of surface area. These measurements come from the saved
channel-103 face/edge/plane graph, not from the SWall driver or an IFC export.

The independent pinned public reader decoded the current channel-103 record in
`Partitions/66` completely: 6,884 bytes, body SHA-256
`aaee54be28c427a29fa62226f5ef8cffe3e830b2174502c5c8cbe845ce8d53f0`.
The audit binds its input to the actual candidate's SHA-256 and records the
reader revision, probe source/binary hashes and decoded-graph JSON hash.

## Native topology and geometry checks

Geometry object 5 contains six faces, twelve edges and eight vertices. The
verifier independently resolves graph pointers, follows each face loop's
`m_next`/`m_prev` links, checks ownership, and reconstructs world-space endpoints
from each face's native plane and UV coordinates. Endpoint continuity determines
edge direction within the stored loop; no convention for `m_orientFlag` is
assumed.

All twelve solid edges have incidence two and opposite directed traversal in
their adjacent face loops. Euler characteristic is two. Every face is planar,
convex and nondegenerate, and the closed solid passes outward half-space
convexity checks. Fan triangulation of the native polygons produces signed
volume `120.00000000000085` cubic feet. The translated native bounds are:

- Minimum: `(519.5, 67.41666666666657, 76)` feet.
- Maximum: `(531.5, 68.08333333333329, 91)` feet.

Those bounds match both saved channel-103 bounding boxes and the independently
decoded channel-101 Outline. They measure 12 × 2/3 × 15 feet. Four additional
one-face Geometry components are open sheets, each with four boundary edges;
they are reported separately and excluded from solid volume. Their broader
native semantic role is not inferred.

The original tracked profile measures 95 cubic feet through the same native
BRep verifier. Its driver starts at parameter -0.25; the stretching code's
combination of transformed origin and scaled endpoint parameters preserves the
actual start point correctly. Affine plane origins and UV scaling agree for
basis vectors parallel or perpendicular to the stretch axis.

## Review findings and scope

The measured profile's two channel-102 GElement caches have empty sentinel
bounding boxes. Its parameter set contains height and offsets, with no explicit
length/area/volume cache identified. This observation does not establish that
all wall profiles lack such caches. The encoder now rejects nonempty unhandled caches, additional driver lines,
nonfinite source parameters, and non-world-axis-aligned profiles whose
transformed axis-aligned box would no longer be a tight box. It also requires
the measured 24 paired face endpoints. These are explicit supported-profile
guards, not claims of arbitrary wall support.

Five tests verify source solid topology/volume and reject broken links,
disconnected UV endpoints, nonfinite planes, stale bounds and duplicate faces.
The verifier supports convex single-loop planar faces only; holes, curved edges
and face regions fail explicitly. Closed manifold geometry is a stronger check
than pairwise endpoint agreement, but it does not prove Autodesk acceptance or
complete native document semantics.

```sh
python3 research/rvt/wall_brep_audit.py research/rvt/local/wall-parametric-candidate-independent-graphs.json --candidate research/rvt/local/wall-parametric-candidate.rvt > research/rvt/results/wall-brep-audit.json
python3 research/rvt/wall_brep_audit.py research/rvt/results/wall-element-profile.json
python3 -m unittest discover -s research/rvt -p test_wall_brep_audit.py
```
