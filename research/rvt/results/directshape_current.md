# Experimental current-schema DirectShape wrapper

An explicitly hypothetical Revit2024 DirectShape now has complete independently
decodable101/102/103 bodies, containing one newly encoded closed cuboid mesh.
This is an element-body experiment, not a saved or accepted native document.

The schema encoder emits193-byte101 (three objects),962-byte102 (six objects)
and530-byte103 (three objects). The pinned public decoder consumes every byte
and reproduces every semantic field, including fresh self/geometry-owner133210.
The independent decoded103 topology contains8 vertices and12 triangles, has
opposite paired edges and closed vertex links, and measures volume
7.986000411093227 cubic feet after float32 quantization. The input dimensions
are1.1×2.2×3.3 feet at(0.1,0.2,0.3). See `directshape_current.json` for exact
body hashes, quantization error and geometry checks.

## Evidence versus hypotheses

Measured2015 instance structure supplies null type/level/phase/family references,
null GeomTable/GeomSteps, DirectShapeCell and DirectShapeDataCell layout. Actual
2024 declarations supply all field encodings. The measured current terrain mesh
supplies GPolyMesh wire fields; the native_mesh encoder supplies independently
checked closed FacetedTopology0 vertices/indices/normals. Current style113 and
interior style119 are explicit caller dependencies, with category-2000011.

The following remain hypotheses, not inferred safe native defaults:

- Each2024 DirectShapeOptions enum/capability value. The caller must supply all
  eight values explicitly; no implicit default profile is accepted.
- Identity position, null reference cell and canCreatePartsStatus0 as native
  instance lifecycle choices.
- Historical header flags8488 and reconstructed deletion parents.
- Historical type-less/no-history structure in a2024 instance.
- Terrain mesh flags/control command used inside DirectShape, and normal/shading
  semantics. Mathematical closure does not prove native solid interpretation.

The constructor requires `acknowledge_hypotheses=True`. Its evidence retains each
hypothesis and explicit option value. The fresh application GUID/dataID/name are
research metadata; no vendor application identity is reused.

`construct(schema, mesh_profile, legacy_root, new_id, points, triangles, config,
acknowledge_hypotheses=True)` returns body bytes, semantic graphs and audit. The
caller must independently allocate the fresh ID, add full save metadata and
register dependencies. This constructor does not implement those document steps.

## Reproduction and limits

```sh
python3 research/rvt/directshape_current_experiment.py \
 --schema research/rvt/local/directshape-core-schema.bin \
 --profile research/rvt/results/directshape-mesh-profile.json \
 --legacy research/rvt/results/directshape_legacy_audit.json \
 --probe /tmp/rvt-wall-candidate-target/release/rvt-wall-candidate-probe \
 --output research/rvt/local/NEW-directshape-current-run \
 --result research/rvt/results/directshape_current.json
python3 -m unittest discover -s research/rvt -p test_directshape_current.py
```

Four tests pass, including explicit-hypothesis/options rejection. The experiment
compares complete independently decoded fields, ignoring only physical pointer
offsets added by the reader. Its geometry checks use actual decoded103 values.
No saved-document projection or IFC export was performed. A source search found
no explicit DirectShape option interpreter in the pinned public reader; generic
export behavior must be tested on a fully registered candidate. No Autodesk
acceptance, complete arbitrary-mesh authoring or standalone document creation is
claimed.

Generated normals were corrected to one normal per triangle after the public saved-graphics reader rejected the earlier per-vertex cardinality. The latest report and bodies were regenerated and independently decoded; historical reports remain scoped to their recorded hashes.
