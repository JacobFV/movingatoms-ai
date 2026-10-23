# Native mesh / DirectShape feasibility (2026-10-22)

The measured native format can serialize triangle-mesh geometry. A standalone
DirectShape authoring route is **not yet established**. The runnable experiment
below reproduces native mesh-bearing records byte for byte without copying opaque
bodies. It deliberately does not relabel a terrain element as DirectShape.

## Corpus and current routing

`directshape-inventory.json` binds six MIT-licensed fixture hashes and the public
reader revision `b6086d41b9758fd9b92f42f0a47b8345b9c58056`. There are no current
DirectShape instances in those fixtures. The sole current DirectShapeType is
core2024 element130286, Facade, category-2000011, Partitions/53, revision34.

Its three channels decode completely with raised graph budgets:101 has193 bytes
and3 objects;102 has15,639,178 bytes and144,380 objects;103 has16,514,325 bytes
and172,317 objects. The initial100,000-value budget failed inside GeomTable;
`directshape-default-budget-inventory.json` retains that negative result. The
successful probe uses10,000,000 values and500,000 objects. These are decoder
resource limits, not a demonstrated unknown encoding.

This type contains4,657 six-face planar BRep solids,27,942 faces and55,884 edges,
not GPolyMesh geometry. DirectShapeCell holds source geometry; GeomStepList holds
DirectShapeCopyAndTagGStep, with curve/face/edge histories and88,487 GeomTable
entries. This is not a minimal arbitrary-mesh instance template.

`directshape-incoming.json` independently checks typed ElementId references over
79,275 routed current records (26,425 elements). Only the type's own header and
self-ID refer to130286. Embedded groups are excluded, explicitly recorded in the
audit; the result does not establish absence of references in embedded content.

## Measured native triangle mesh

`directshape-mesh-inventory.json` records a full current-core graph survey of79,275 records with zero unsupported
records. Eight records contain GPolyMesh, belonging to SiteSurface elements21930,
21933,21971,21974. The smallest103 bodies are867 bytes. The durable
`directshape-mesh-profile.json` contains all three complete graphs for21974,
source body hashes, source fixture hash and minimal structural declarations.

The103 graph contains GElement, GFilter, two GPolyMesh, GConditionInt and two
FacetedTopology0 objects. FacetedTopology0 stores float32 vertex/normal triples
and int32 triangle-index triples. One component has14 vertices and12 triangles;
the other has4 vertices and2 triangles. These are open terrain components, not a
measured closed DirectShape mesh. SiteSurface102 additionally needs terrain
TriangulationDriver/Memento and ContourManager semantics.

From the repository root:

```sh
python3 research/rvt/directshape_mesh.py research/rvt/results/directshape-mesh-profile.json
python3 -m unittest discover -s research/rvt -p test_directshape_mesh.py
```

The schema encoder reconstructs101/102/103 bodies of237/1732/867 bytes and checks
each against the independently decoded source body's SHA-256. Optional
`--output NEW_DIRECTORY` writes those bodies. Three tests cover exact output,
changed-vertex rejection and missing-channel rejection. This API is intentionally
source-exact; arbitrary mesh replacement needs additional semantic validation.

## Dependencies and registration

Measured type130286 depends on GStyle113 (wall category, material87), filling
style119, material130287 and appearance asset130288. Its header deletion list
contains its category, self and material. Material130287's header additionally
references appearance130288. Reusing those objects retains donor context.

`directshape-global-registration.json` binds a saved Global graph to the exact
inflated original stream bytes (excluding four zero padding bytes). Typed hits
place130286 in ElementTrackingData's wall-symbol set and in
AppInfoSystemFamiliesNames; material130287 appears in MaterialTracking and
appearance130288 in AppearanceAssetTracking. These are observed source
registrations, not proof that all creation-time requirements are identified.

Schema declarations also expose DirectShape's instance transform, typeId,
DirectShapeDataCell application IDs/name/category, geometry/ref/plan cells and
options including RoomBoundingOption. No measured current instance in this
corpus establishes correct defaults or complete instance registration behavior.

## Bounded next steps and acceptance boundary

1. Find a licensed DirectShape instance fixture and decode its complete three
   channels, transform, dependencies and global registration.
2. Build a small closed manifold mesh with explicit normals, winding, edge
   incidence and volume checks; round-trip its FacetedTopology0 through the
   independent public decoder. Existing terrain records prove field encoding,
   not closed-solid semantics.
3. Establish minimal DirectShape geometry histories/tags and category/material
   closure from measured instances; compare native graph and independently
   projected geometry after writing.
4. Author a coherent minimal document context rather than retaining the donor
   building. Mesh serialization alone does not solve document bootstrap,
   registrations, revision/allocation state or signed-section acceptance.

No edited native RVT was generated by this feasibility audit, and no Revit or
Autodesk acceptance is claimed. Public-reader decode and IFC projection remain
separate evidence from native application acceptance.
