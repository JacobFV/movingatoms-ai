# Creation, modification and user-modification evidence

The static corpus does **not** determine whether the room-finish edit must
advance `m_lastUserModificationDate` from 639 to 703. That field name suggests a
user-edit distinction, but the distribution is not a sequence of controlled
before/after saves. Leaving it unchanged and updating it are both hypotheses.
No production save rule is inferred here.

`modification_history.py` independently decodes all 53,544 project identities
with the pinned public clean-room schema reader
`b6086d41b9758fd9b92f42f0a47b8345b9c58056`. Counts across six licensed files:

| Relationship | Records |
| --- | ---: |
| Creation = user modification = modification | 41,627 |
| Creation = user modification < modification | 5,434 |
| Creation < user modification = modification | 2,969 |
| Creation < user modification < modification | 1,939 |
| User modification is `0xffffffff` | 1,575 |

All creation and last-modification values are within their file's History
range. Every out-of-range user-modification value is exactly `0xffffffff`;
these are observed sentinel-shaped values, not valid episode indices. The
report lists exact affected IDs and per-file counts. Do not reject a source
file merely because this field is not an in-range History episode.

## Schema spans and room effect

Embedded-schema traversal establishes these row-relative spans in both the
28-byte and 40-byte ElemRec profiles:

| Schema field under `m_history` | Bytes, end exclusive |
| --- | --- |
| `m_creationDate` | 8..12 |
| `m_lastModificationDate` | 12..16 |
| `m_lastUserModificationDate` | 16..20 |

Architecture room 348738 has its row at inflated ElemTable offset 109206,
so its three fields start at 109214, 109218 and 109222. Source values are
639, 687, 639. Its original ID suffix is 348738 and its native UniqueId is
`c1104319-15e9-42d2-b2f7-40d05b0bb07c-00055242`.

The audit appends the same deterministic History episode used by the candidate,
then independently parses two in-memory table variants:

- Last modification 703, user modification unchanged at 639.
- Last modification 703, user modification advanced to 703.

Both retain the exact native UniqueId and every unrelated identity. The only
room identity differences are the explicitly changed revision fields and their
raw serialized words. This is expected from the pinned reader:
`native_index.rs::parse` constructs UniqueId from **creation episode and original
ID suffix**, while `native_document.rs` routes using `stored_revision` (last
modification). `other_revision` (user modification) is exposed as metadata and
is not used by this reader's route selection. Reader success consequently
cannot establish which user-modification behavior Revit expects.

## Native record evidence and its limits

One channel-101 record per fixture is decoded through its embedded
`ElementHeader` root schema, with exact source stream, element ID, body hash,
field names and spans in the JSON. Architecture's selected sample is the same
room: `Partitions/80`, record 348738. Its `m_regenHistory.m_historyMap` is empty
at body bytes 2..6; the decoded root ends at byte 76 of a 249-byte body.
None of the decoded root field names is the project-table modification-history
triple. The remaining 173 bytes include deferred data and are **not** claimed
fully interpreted by this audit. The other five representative roots also
have empty regeneration maps; this does not prove all model records do.

Channels 102 and 103 are not schema-decoded in this audit. The prior candidate
experiment preserves them except for the explicit parameter edit and object
checksums. There is no evidence here permitting a universal claim that all
native object data is independent of these episodes.

Reproduce:

```sh
python3 research/rvt/modification_history.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/schema-target \
  research/rvt/local/bookkeeping.json research/rvt/local \
  > research/rvt/results/modification-history.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_modification_history.py -v
```

Two tests verify relationship classification and separate out-of-range field
reporting, including the observed sentinel. No modified RVT is emitted by this
audit, no proprietary implementation was inspected, and no Autodesk acceptance
is claimed.
