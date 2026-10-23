# Triangle surfaces and signed16 primitive chunking

`native_mesh_surface.encode_surface` is separate from the closed-solid encoder. It accepts triangle surfaces in feet and preserves face order and winding. Open boundaries, disconnected components, nonmanifold edges and inconsistent paired-edge winding are explicitly reported; none are silently repaired or interpreted as solid volume. Self-intersections are not checked by this surface API.

The encoder requires finite XYZ coordinates, valid triangle indices and nondegenerate, nonduplicate faces. It welds only numerically identical input positions and records the complete original-to-welded vertex mapping. Distinct positions that collapse under float32 quantization are rejected. Degenerate quantized triangles and orientation changes of 90 degrees or more are also rejected. Isolated unused points are unsupported and rejected rather than silently discarded. Normals are generated per triangle from the quantized positions; vertex seam welding therefore does not average shading normals across faces.

Triangles are assigned in original order to primitives with at most 32,768 local vertices. Each primitive uses signed16 local indices, preserving every triangle even when the complete input has larger global indices. Its audit records global-to-local vertex membership and original face indices. Shared boundary vertices may occur in multiple chunks, with exactly equal quantized positions. Chunking never truncates faces.

Five focused tests pass. The public reader independently decodes diagnostic GElement/GPolyMesh wrappers and expands them through `native_saved_mesh::graphics` for three cases:

| Input | Input vertices | Triangles | Primitive vertex counts | Result |
| --- | ---: | ---: | --- | --- |
| Open plane | 4 | 2 | 4 | Four boundary edges; exact rendered triangles |
| Two disconnected planes | 8 | 4 | 8 | Two edge-connected components; exact rendered triangles |
| Large-index triangle surface | 33,000 | 11,000 | 32,766 and 234 | Every rendered triangle preserved in order |

The large case verifies actual signed16 chunking beyond the per-primitive index limit. The independent decoder uses an explicit resource budget of 1,000,000 values, 100 objects and depth 128; these are implementation bounds, not format limits. The test compares rendered vertices against separately float32-quantized original face coordinates, checks expanded triangle order and verifies normals against face winding. [Machine-readable evidence](native-mesh-surface.json) binds the input profile and records each primitive hash/count and all preservation checks.

```sh
python3 -m unittest discover -s research/rvt -p test_native_mesh_surface.py
python3 research/rvt/native_mesh_surface_experiment.py \
  --reader /home/brandonin/.cache/movingatoms-rvt-rs \
  --target research/rvt/local/new-element-build/target \
  --schema research/rvt/local/core2024.schema \
  --profile research/rvt/results/directshape-mesh-profile.json \
  --result research/rvt/results/native-mesh-surface.json
```

The return value contains `components`, each with encoded topology bytes, schema fields and chunk audit, plus a global `report`. A separate constructor can wrap those components in multiple GPolyMesh primitives. This checkpoint does not create a DirectShape instance or document and does not establish Autodesk acceptance. Metres-to-feet conversion belongs to the caller; this encoder's input and error report explicitly use feet.
