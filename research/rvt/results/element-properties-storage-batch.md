# Shared schema and attached owner metadata controls

One fresh schema can now register multiple owner IDs, and its entity can be serialized directly into a DirectShape or wall's common Element cell list. Independent decoding recovers the attached values while preserving every original owner and geometry field except the intended cell-list addition. Attachment remains a lifecycle hypothesis: no source fixture demonstrated this exact own-schema attachment and no native application acceptance is established.

`element_properties_storage_batch.py` owns two interfaces:

- `register_schema_and_owners(raw, graph, declarations, owner_ids)` requires sorted unique positive owner IDs. It registers our schema once, records every owner under its `EStorageTracking` GUID, and adds every owner to cell key `-100`. The original three registration objects must reconstruct byte-exactly. Existing schemas and unrelated global graph semantics remain preserved. Existing own-schema registration and previously tracked owner IDs are rejected rather than silently migrated.
- `attach(graph, declarations, source_body, application_id, name, properties, acknowledge_hypotheses=True)` requires an independently decoded full graph with edges and byte-exact source reconstruction. For a null cell pointer it creates a CellList; for a preexisting owned CellList it appends one ESEntityCell. It writes only our own scalar-string entity and reconstructs FIFO object order from the measured graph edges. Existing ES entities and unsupported/shared cell ownership are rejected. It returns the new body and a change report; the caller must independently decode the result and register the owner.

The three scalar strings retain the same schema GUID `3e6dd92d-a1e2-5529-bf69-045c18c5f87b` and application semantics documented in `element-properties-storage.md`. No vendor schema is reused. Native geometry, names, identifiers, and shared-pointer tokens are preserved. On a DirectShape the caller can use its native `m_appDataGUID` as the own entity's `ApplicationId` to establish an explicit mapping; this audit does not silently impose that mapping.

## Independent controls

| Owner | Source | Source body | Attached body | Existing CellList |
|---|---|---:|---:|---|
| DirectShape 2746 | Verified research candidate `a971271…` | 986 bytes | 1262 bytes | Null; created |
| SWall 20826 | Licensed Core2024 `c805df44…` | 2946 bytes | 3206 bytes | Owned; appended |

Both output bodies fully decode using the dynamically discovered own catalog. Exact metadata includes nested JSON, a boolean, and supplementary Unicode. Removing only the new entity/cell and restoring the original cell-list state yields the exact original normalized object sequence and all original field values, including geometry. The output hashes and exact source file/body hashes are in `element-properties-storage-batch.json`.

The separate minimal-seed registration control registers owners `[2746,2747]` under exactly one schema; independently decoded full Global fields and edges equal the expected graph. The Core wall's ID20826 is not falsely registered in that seed: its attachment is a body-only encoding control. A combined document builder must allocate IDs centrally, supply corresponding bodies, register the actual attached IDs, perform save bookkeeping, and audit the saved file.

## Reproduction

```sh
python3 research/rvt/element_properties_storage_batch_audit.py --reader /home/brandonin/.cache/movingatoms-rvt-rs --target research/rvt/local/schema-target research/rvt/local > research/rvt/results/element-properties-storage-batch.json
python3 -m unittest discover -s research/rvt -p test_element_properties_storage_batch.py
```

All three focused tests pass: the measured wall output matches the independent audit hash, input graph immutability is checked, and altered source bytes, missing acknowledgment/edges, and malformed owner lists are rejected. The public reader is pinned in the machine-readable report; all three source files are hash-checked before use. This audit emits bodies and a modified Global payload under ignored local storage, not a complete combined RVT.
