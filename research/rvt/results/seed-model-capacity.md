# Maximum-owner saved-model capacity check

The frozen standalone runtime completed the full writer, metadata and independent saved-scene pipeline for 100 new owners. Candidate SHA-256: `9f6e268933116c3e163b8fb2b96483d3015aa2fefba2f3845c47d36c41d9fb33`.

[The request](seed-model-capacity-request.json) contains no new levels and one triangle per owner. It cycles through 20 existing category/style/material contexts, five owners per category. Every owner carries a distinct application ID and nested properties including Unicode, arrays, booleans, nulls and numeric measurements.

The saved-file audit establishes:

- Exactly 100 unique native IDs 2746–2845, 100 unique native UniqueIds and100 unique application IDs.
- The owned extensible-storage schema registers exactly those 100 owners; all nested application properties match the request.
- All 100 oriented triangles render after the declared metres-to-feet/float32 conversion, with one primitive per owner.
- All 20 category/style/material contexts resolve through the unchanged seed records.
- All 2,300 original native identities and the original partition are preserved; unrelated Global semantics remain unchanged.

These are generic DirectShape triangle-surface owners assigned to existing categories. They are not native parametric walls, doors or other families. No solid-volume, regeneration or Autodesk acceptance claim follows from this capacity result.

The immutable run used `runtime-bundle-v1` with `/usr/bin/python3 -S`, without relying on live research code. [The compact report](seed-model-capacity.json) records its bundle manifest hash, request/candidate hashes, all registration owner IDs, category/material context summaries, and hashes of the full transport, metadata, native and saved-scene evidence. A later bundle validator hardening produced v2; this report deliberately retains the exact v1 runtime used for this run.

```sh
/usr/bin/python3 -S research/rvt/local/runtime-bundle-v1/run.py \
  --request research/rvt/results/seed-model-capacity-request.json \
  --output research/rvt/local/new-capacity-run \
  --acknowledge-hypotheses
python3 -m unittest discover -s research/rvt -p test_seed_model_capacity.py
```

Both focused boundary tests pass: exactly 100 owners are accepted with the expected allocation, and a 101st owner is rejected by both the request validator and independent audit contract. The full ignored run is in `research/rvt/local/seed-model-capacity-100/`; its verified artifact is `verified-candidate.rvt`.
