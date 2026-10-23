# Saved minimal-seed application metadata control

A complete candidate compound file now contains a fresh DataStorage owner and our own registered metadata schema. The pinned public reader extracts the actual saved native records, discovers the schema through the saved file's owned Global catalog, and recovers the exact application ID, name, and nested JSON. This establishes the listed local file/reader checks; native application acceptance remains untested.

## Evidence

- Source SHA-256: `674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe` (licensed minimal seed).
- Candidate SHA-256: `1649a4c383bb742c4b6b8c8edd3ad253a09fc2c0d7c7f4d1ad1ee4bd90a5e6f5`.
- Reader commit: `b6086d41b9758fd9b92f42f0a47b8345b9c58056`.
- New owner: 2746, native `DataStorage`, all three channels routed from `Partitions/1` and fully consumed independently.
- All 2300 source table rows remain byte-identical; the source partition stream remains byte-identical. New table count is 2301; history advances from one to two episodes, preserving the original episode. Prior increment rows remain unchanged.
- Rust patch and verify commands pass compound-file transport/page verification. The metadata auditor reads the actual file independently of the builder plan and requires the declared changed Global stream.
- Saved Global bytes equal the schema-registration encoder output; the independent full Global graph matches exactly the intended changes and preserves all unrelated fields and edges.
- The saved catalog contains exactly our fresh GUID `3e6dd92d-a1e2-5529-bf69-045c18c5f87b`, with scalar `ApplicationId`, `Name`, and `PropertiesJson` fields. No vendor schema entity is inherited.
- Exact recovered values are application ID `movingatoms:item-42`, name `Application wall 😀`, and properties with nested height 3.2, true boolean, Unicode list, and null. The only positive owner reference is 2746 itself.

`seed-properties-experiment.json` records the candidate and validation report hashes. `seed-properties-saved-native.json` records actual saved-file public-reader output, including dynamic catalog provenance, for reproducible corruption tests. Raw streams, manifests, and the candidate remain in ignored local storage.

## Reproduction

Use a fresh output directory; existing destinations fail without modification.

```sh
python3 research/rvt/seed_properties_experiment.py --source research/rvt/local/minimal_seed-Project.rvt --output research/rvt/local/seed-properties-control-v2 --reader /home/brandonin/.cache/movingatoms-rvt-rs --target research/rvt/local/schema-target --acknowledge-hypotheses > research/rvt/results/seed-properties-experiment.json
python3 -m unittest discover -s research/rvt -p test_seed_properties_experiment.py
```

Four focused tests cover actual saved values/catalogs, wrong partition routing, incomplete graph consumption, missing channels, altered schema, changed nested values, explicit hypothesis acknowledgment, and no-clobber output. The final runner snapshots research and transport code, writer bytes, source bytes, and seed save-context evidence; publication as `verified-candidate.rvt` requires unchanged inputs/tools and matching candidate hashes from both independent metadata and native checks. The word verified refers only to these recorded checks.

## Remaining limits

Unsigned append partition acceptance, own-only DataStorage lifecycle, schema/owner registration sufficiency, saved dirty-state policy, and ancillary revision/timestamp policies remain explicit hypotheses. This does not establish a complete Autodesk save transaction or production native export. The DataStorage is a separate application metadata record associated by application ID; it does not silently attach properties to a wall, create schedulable Revit parameters, or establish geometry parity. See `element-properties-storage.md` for the source-exact registration controls and public API/schema provenance.
