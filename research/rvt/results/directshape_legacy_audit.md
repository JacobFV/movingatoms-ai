# Historical DirectShape instance evidence

The Apache-2.0 DynamoRevit `singleDirectShape.rvt` fixture is actually Revit2015,
including the identical blob on its Revit2024 branch. Its SHA-256 is
`3b05630eb71230b567b891f7829a9a6326b435b002b99d571d3830790fe50431`.
This audit does not pass a substituted version to the current-document reader.

The embedded2015 Formats schema parses directly. The public physical segment
walker validates both partitions, all298 groups and78,570 physical records.
The measured record header has32-bit IDs; unlike the modern contract, declared
body size equals the sum of body lengths **plus four bytes per record** (the
trailing length). Every record has matching leading/trailing body lengths and
every group matches that accounting and declared object count. Gzip integrity
and continuation framing are checked by the public segment walker.

Two physical DirectShape instances were found,308799 and308800. All six channel
bodies decode completely; source-exact schema re-encoding reproduces every byte.
The native graphs are retained locally in `directshape-legacy-records.json`;
`directshape_legacy_audit.json` records body hashes, object counts, complete
representative wrapper objects, physical framing statistics and declarations.
Current identity/revision routing has not been validated for this historical
file, so these are physical instance records, not an asserted current inventory.

Both instances have typeId=-1, null geometry-history/GeomTable pointers, null
level/phase/family associations, a DirectShapeCell and DirectShapeDataCell.
The shape-data cell holds application GUID, application-data string, name and
category-2000151. Header deletion parents include category-2000151, style17881,
object308797 and self. These external objects still require a dependency audit.

Geometry is planar BRep, not GPolyMesh: instance308799 contains one Geometry
with5,280 triangular faces/7,920 shared edges;308800 has2,168 faces/3,252 edges.
This is useful evidence that measured historical DirectShape instances can
store independent shape geometry without a type or GeomTable. It does not
establish current-version GPolyMesh instance semantics or closed-solid validity.

Compared with2015, the2024 DirectShape declaration adds `m_options`,
`m_oRefsData`, `m_position`, and `m_canCreatePartsStatus`. The old schema has no
DirectShapeOptions class. Therefore2024 defaults, transform behavior, option
semantics and registration cannot simply be copied from this fixture. All
compared structural declarations are included in the JSON, including type-width
changes in their referenced classes.

## Reproduction

`directshape_legacy_probe.rs` is a small standalone binary depending on the
pinned public reader, anyhow and serde_json. Its arguments are the inflated
embedded schema followed by checksum-unpaged partition bytes. Build scratch
and binary are currently `local/directshape-legacy-build` and
`/tmp/rvt-wall-candidate-target/release/rvt-directshape-legacy-probe`.
Run it against `local/directshape-legacy-schema.bin` and
`local/directshape-legacy-partition-{1,2}.bin`, retaining JSON locally, then:

```sh
python3 research/rvt/directshape_legacy_audit.py \
 research/rvt/local/directshape-legacy-records.json \
 research/rvt/local/directshape-legacy-schema.json \
 research/rvt/local/directshape-core-schema.json \
 research/rvt/results/directshape_legacy_audit.json
```

The schema/body encoder uses complete decoded fields, never opaque byte cloning.
No native file was modified and no Autodesk acceptance was tested.

## Historical Global reference audit

`directshape_legacy_global.py` independently decodes the exact2015 Global/Latest
body (56,836 bytes plus four terminal zero bytes),422 graph objects, and checks
source-exact re-encoding. Among7,315 schema-typed ElementId values, neither308799
nor308800 occurs. A separate raw signed32-bit byte search also finds neither ID.
The complete empty hit lists and source/inflated hashes are in
`directshape_legacy_global.json`. No category-2000151 entry is present in
ElementTrackingData's `m_elems` or `m_symbols` arrays. This observed absence does
not justify suppressing required current-version registration: historical
current identity routing and current-version lifecycle semantics remain separate
unresolved questions.
