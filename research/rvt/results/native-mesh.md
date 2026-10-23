# Standalone closed native mesh components

`native_mesh.py` encodes new closed `FacetedTopology0` components using the measured schema layout. It does not create a GPolyMesh wrapper, terrain element, DirectShape instance or RVT document. The source terrain remains identified as terrain.

The measured representation stores points and normal vectors as float32 triples. Its triangle indices are **signed16 triples**, not int32: the nested schema descriptor is base3, modifier0x10, fixed count3. This agrees with the public decoder's signed16 scalar interpretation. The helper limits indices to 0–32767 and rejects unreferenced/duplicate vertices and invalid index types.

Both original terrain components are reconstructed exactly: their encoded field bytes match their original spans within the source-exact channel103 record. Adding only their schema class tag produces standalone components that the independent public reader decodes to the original fields. Their original open surfaces are not claimed to be closed solids.

For new geometry, the default helper validates a single closed convex component: nondegenerate triangles, outward winding, opposite paired edge incidence, connected faces, a single cycle in every vertex link, Euler characteristic 2 and positive signed volume. Convex face-plane checks reject unsupported concavity/intersection. It stores one outward unit normal per triangle. This corrects the first component-only experiment, which generated one normal per vertex: structural decoding accepted that layout, but the public saved-graphics reader rejects eight normals for twelve cuboid facets. Original terrain components retain their exact measured normal arrays; their source-exact structural decode is a separate claim from saved-graphics acceptance.

The pinned public reader accepts normalsFlag0 with either an empty array or exactly one normal per triangle. A new diagnostic GElement/GPolyMesh wrapper is independently decoded and passed to `native_saved_mesh::graphics`. Cuboid, L-prism and torus primitives expand to exactly the expected vertices and normalized facet normals. The eight-normal/twelve-facet negative control is rejected with `unsupported normal cardinality`; an empty-normal fallback is accepted. These tests are recorded in [native-mesh-scene.json](native-mesh-scene.json). The diagnostic wrapper is not an authored element or DirectShape.

All checks run before and after float32 quantization, so quantization-collapsed vertices or degenerate geometry are rejected. Twelve focused tests pass, including open/reversed/duplicate faces, invalid indices, nonfinite values, concavity and large-coordinate float32 collapse.

The public reader independently decodes two source components and the following new components with exact field equality:

| Component | Bytes | Vertices / triangles | Decoded volume | Maximum coordinate error | Volume error |
| --- | ---: | --- | ---: | ---: | ---: |
| Tetrahedron | 150 | 4 / 4 | 1.331000068515538 | 9.536743172944284e-8 | 6.851553790987452e-8 |
| Cuboid | 342 | 8 / 12 | 7.986000411093227 | 9.536743128535363e-8 | 4.110932261269795e-7 |

Coordinates use feet in this experiment; volumes therefore use cubic feet. Maximum vertex displacement is approximately 9.61212e-8 feet for the tetrahedron and 1.43051e-7 feet for the cuboid. Maximum float32 normal unit-length error is below 3.7e-8 across the four generated components. [The evidence report](native-mesh.json) records every input coordinate and index, individual rounding errors, source field-span hashes, new body hashes and independent decode results.

```sh
python3 -m unittest discover -s research/rvt -p 'test_native_mesh*.py'
python3 research/rvt/native_mesh_experiment.py \
  --schema research/rvt/local/core2024.schema \
  --probe research/rvt/local/new-element-build/target/release/rvt-wall-element-probe \
  --result research/rvt/results/native-mesh.json
```

These results prove bounded component serialization and geometric consistency. They do not establish instance defaults, material/category dependencies, document registration, native regeneration, smooth/flat shading behavior or Autodesk acceptance. A measured real DirectShape instance is still needed for those next stages.

## Opt-in connected nonconvex components

`allow_nonconvex=True` retains edge incidence, face connectivity, vertex-link and finite-value checks while replacing the convexity restriction with bounded triangle-pair intersection checks. Noncoplanar pairs use triangle-plane contacts; coplanar pairs use convex polygon clipping. Contacts are allowed only on the explicitly shared vertex or edge. The audit rejects undeclared touching, overlapping triangles and intersecting surfaces. It runs both before and after float32 quantization, with coordinate tolerance `max(1e-12, extent*1e-10)`; this is a floating-point bounded check, not an exact-predicate geometry kernel. At most 2,048 triangles are supported for this quadratic audit.

Consistent winding plus positive signed volume determines outward orientation for a connected closed nonintersecting shell. Euler characteristic is checked against an orientable closed surface and its genus is reported, allowing tunnels. A nonconvex L-prism has 12 vertices, 20 triangles, genus 0 and exact volume 3 cubic feet; its encoded component has 534 bytes. A triangulated torus has 96 vertices, 192 triangles, genus 1 and decoded polyhedral volume 8.48528176961986 cubic feet; its encoded component has 4,638 bytes. This volume describes the triangulated torus, not the smooth analytic torus. Its float32 volume error is 3.953812868218165e-7 cubic feet. Both independently decode and pass the public saved-graphics path.

Disconnected/multipart shells, open surfaces and triangle soups remain rejected by this closed-component API. Source open terrain can still be reproduced exactly through `source_component`; that does not create a general open-mesh authoring API. Native instance/document creation, Revit regeneration and Autodesk acceptance remain outside this checkpoint.

```sh
python3 research/rvt/native_mesh_scene_experiment.py \
  --reader /home/brandonin/.cache/movingatoms-rvt-rs \
  --target research/rvt/local/new-element-build/target \
  --schema research/rvt/local/core2024.schema \
  --profile research/rvt/results/directshape-mesh-profile.json \
  --result research/rvt/results/native-mesh-scene.json
```
