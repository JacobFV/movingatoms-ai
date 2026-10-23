# Native wall properties: measured Comments encoding and metadata limits

`element_properties.py` now writes the measured native instance Comments field
in the Core 2024 SWall profile. It can replace an existing value or explicitly
create the already-declared string-parameter container when its root pointer is
null. It does not invent a parameter ID, overload Comments with application
JSON, or claim arbitrary metadata/schema registration.

## Source inventory

The pinned clean-room reader independently resolves and fully decodes 1,219
current project SWall graphs across six licensed fixtures:

| Fixture | Current SWalls | With string parameter set |
| --- | ---: | ---: |
| Core Interior | 1,209 | 8 |
| Einhoven | 2 | 0 |
| RE1 Architecture | 8 | 0 |
| RE1 Mechanical / Plumbing / Electrical | 0 | 0 |

This inventory is scoped to project SWall records, not walls inside embedded
content documents or every possible wall implementation. Every selected graph
is complete and follows an exact current-record route. All eight existing
string sets contain serialized parameter **-1010106**, with an empty string
value. None of the 1,219 wall graphs contains an `ESEntityCell`.

Public Autodesk-hosted API discussion identifies `ALL_MODEL_INSTANCE_COMMENTS`
as -1010106 and `ALL_MODEL_MARK` as -1001203 ([Autodesk discussion](https://forums.autodesk.com/t5/revit-api-forum/schedules-and-data/m-p/7715336)).
That is public API naming evidence, not a specification of file serialization.
The Comments wire layout is independently established from the actual eight
source instances. **Mark was not observed in these wall string sets**, so no
Mark encoder is presented as measured source behavior.

## Executed encoding checks

The file-local declarations are:

- `ParamValueSetAString`, tag 3021: `m_paramSet`, descriptor `0x500e`, array of
  `ParamValueAString` (tag 3017).
- `ParamValueAString`: `m_paramId`, inline ElementId (tag 20), followed by
  `m_value`, descriptor `0x6008`, counted UTF-16LE text.

The complete measured declarations are preserved in `element-properties.json`.
Both edited bodies were first reconstructed byte-for-byte from their decoded
source graph, then encoded with the test Comments text and independently
re-decoded by the pinned reader:

| Trial | Source wall | Source bytes | New bytes | Result |
| --- | ---: | ---: | ---: | --- |
| Replace existing empty Comments | 22771 | 4,173 | 4,249 | Full graph matches intended fields |
| Create declared string set from null pointer | 20826 | 2,946 | 3,040 | Full graph matches intended fields |

The new string includes a supplementary Unicode character and occupies 38
UTF-16 code units. Both decoded bodies consume every byte; every other object's
fields, reference tokens and class identity remain as intended. New source
body hashes and output hashes bind the trials in the JSON.

Creation uses the schema-defined string pointer and the measured deferred-object
queue order, inserting the string set before the next root-owned object. It
requires explicit `allow_create=True`; replacement requires an exact old-value
precondition and verified ownership edge. Unknown classes/layouts, shared
parameter-set pointers, ambiguity, embedded NUL and oversized strings fail.

The API returns bytes plus expected object semantics. **Graph offsets and edge
indices change when data grows**: callers must decode the new body to obtain
fresh offsets/edges, rather than reusing source graph metadata. Integrating this
with a candidate also requires partition reconstruction, checksums, proper save
bookkeeping and the remaining authenticity/acceptance work.

## IDs, names and arbitrary application properties

The source SWall graph has no direct `m_name` field to populate. A native element
ID and creation-based UniqueId are not interchangeable with an application's
external ID or display name. Neither Mark nor Comments is silently assigned
those roles by this encoder.

The file-local Extensible Storage catalogs are fully inventoried in the report.
They contain existing application-specific schemas, including Core's
DataStorage identity/exchange, Magnetar, IFC-settings and other vendor schemas,
and Architecture's Guardian/Onuma schemas. Their field declarations do not
establish a Moving Atoms schema. Repurposing those GUIDs/fields to hold arbitrary
application metadata would change their declared meaning and is not implemented.

A complete application-properties solution still needs an independently
qualified schema-registration and entity path, or a declared shared/project
parameter definition/binding path. Creating undeclared serialized parameter IDs
is not supported. These remaining dependencies are explicit; successful Comments
encoding does not establish IFC-equivalent arbitrary property export.

## Reproduce

```sh
python3 research/rvt/element_properties_audit.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/schema-target research/rvt/local \
  > research/rvt/results/element-properties.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_element_properties.py -v
```

The audit builds the checked-in `element_properties_probe.rs` against pinned
public reader `b6086d41b9758fd9b92f42f0a47b8345b9c58056`, freshly extracts the
source graphs/schema, checks all fixture hashes and stores raw source graphs
only in ignored local research storage. No proprietary implementation is used.
Three tests cover explicit creation, source immutability, Unicode, invalid text,
wrong schema/profile and unsupported shared ownership. No RVT file is emitted
by this audit, and Autodesk acceptance remains untested.
