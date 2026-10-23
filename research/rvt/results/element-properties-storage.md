# Fresh application metadata schema: seed and Core controls

The minimal seed already owns an `ESSchemaStorage` through its `AppInfoManager`, with zero application schemas. We can encode a fresh application schema, register a fresh owner in the existing tracking objects, and independently recover its application ID, name, and arbitrary JSON properties from a new DataStorage body. Core provides the nonempty-catalog preservation control. This is an executable serialization hypothesis, not Autodesk acceptance or a complete native save.

`element-properties-storage.json` binds both inputs, inflated Global streams, and three owner bodies by SHA-256. The independent reader is pinned to `b6086d41b9758fd9b92f42f0a47b8345b9c58056`. No proprietary program code was used.

## Own schema and registration

The new GUID is `3e6dd92d-a1e2-5529-bf69-045c18c5f87b`, UUID5 of the Moving Atoms schema URL `https://movingatoms.com/schemas/native-rvt/application-properties/v1`. This URL is a namespace identifier, not a claim that a schema has been published there. The schema name is `MovingAtomsElementPropertiesV1`. Its three fields, indexed 0–2, are `ApplicationId`, `Name`, and `PropertiesJson`, all scalar `TCHAR` strings. Vendor ID and application-access GUID are empty/zero; read/write levels use measured value 1. We do not reuse vendor schema GUIDs, fields, identity entities, or exchange policies.

The public [SchemaBuilder API](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/e74f9357-cc3c-558e-73b8-38ce6d247869.htm) documents caller-supplied schema GUIDs and access configuration; [AddSimpleField](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/5de0ea30-a58e-4db2-373c-05222a139465.htm) supports string scalar fields. These establish intended public semantics, not the binary layout. The layout comes from file-owned schema declarations and the public reader's `native_es_catalog` and `native_parameters` implementations.

`register_schema_and_owner` reconstructs each original target object's bytes exactly before replacing it. It adds the schema to `ESSchemaStorage.m_storedSchemas`, adds its GUID and owner to `EStorageTracking.m_trackingItems`, and adds the owner to cell type `-100` in `ElemsSetWithCellsTracking.m_elemIdSetMap`. GUID maps retain measured GUID-byte ordering; integer maps/sets retain ascending order. Existing Forge and parameter schemas, all other application schemas, and all other Global graph fields and edges remain semantically identical under independent decoding. The existing document ownership pointers remain unchanged. Saved `m_dirty=0` is preserved; this is an explicit save hypothesis.

| Source | Catalog before → after | Fresh owner | Cell tracker source span | Schema storage source span | ES tracker source span |
|---|---:|---:|---|---|---|
| Core 2024 | 8 → 9 | 133210 | 99551–99735 | 100619–996525 | 999827–1000067 |
| Minimal seed | 0 → 1 | 2746 | 55343–55415 | 55707–820431 | 823349–823357 |

Spans are half-open offsets in the inflated Global/Latest payload. Minimal seed lacked cell key `-100`; the encoder adds it explicitly. The audit allocates `ElemTable.last_id+1` and checks absence from current project IDs. This allocation is local to the audit: integration must allocate centrally with other new elements.

## Own owner and arbitrary properties

`owner_bodies` emits a fresh DataStorage with only our entity, not a copied vendor DataStorage. Channels 101/102/103 are 119/417/2 bytes for the recorded example. Independent decoding consumes each entire body; their only positive ElementId reference is their new owner itself. The catalog is independently discovered from the modified Global stream rather than manually supplied schema metadata. The decoder then reports one `ExtensibleStorageEntity` with exactly our GUID and all three exact values.

The example includes a nested dimension, boolean, list, supplementary Unicode character, and null. JSON is deterministic and roundtrips without coercion. Non-string keys, tuples, NaN/infinity, non-JSON objects, and invalid/oversized native strings are rejected. JSON-escaped NUL is valid inside properties; raw NUL in the native application ID/name is rejected. `PropertiesJson` is an application data container, not a claim that its keys become native schedulable parameters.

The DataStorage owner is a separate metadata record. Its `ApplicationId` is available to the application as the association key; no implicit attachment to a wall or DirectShape is claimed. DirectShape's native identity/name fields are a separate implementation. Creating multiple owners, reusing an existing own schema, and schema migration are not implemented here: registration deliberately rejects an already-present own GUID.

## Reproduction and boundaries

```sh
python3 research/rvt/element_properties_storage_audit.py --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --target research/rvt/local/schema-target research/rvt/local > research/rvt/results/element-properties-storage.json
python3 -m unittest discover -s research/rvt -p test_element_properties_storage.py
```

Both fixture audits pass; all four focused tests pass. Generated raw bodies/catalogs stay under ignored `research/rvt/local/`. This audit does not emit a complete RVT, update save history, allocate multiple related elements, or prove native application acceptance. The own-only entity DataStorage and fresh registration are deliberately identified as new hypotheses despite exact independent decoding. The source-exact controls establish preservation and reader agreement, not completeness of undocumented save rules.
