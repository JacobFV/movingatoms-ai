# File identity and coordinated-save linkage

Six licensed fixture audits establish relationships that previous experiments
left inconsistent. The evidence in `save-identity.json` is extracted from file
bytes using the pinned public reader at
`b6086d41b9758fd9b92f42f0a47b8345b9c58056`, with source hashes, field spans and
exact decode boundaries. No Revit executable or proprietary SDK was inspected.

## Contents revisions

`Contents` uses the recovered page ECC, including final-page length framing.
After unpaging, its gzip starts at byte 91 in the 2023/2024 fixtures and byte 24
in all four 2025 fixtures. The gzip ends exactly at logical EOF. Treating the
stored stream as raw gzip had incorrectly made its ECC appear to be a suffix.

The inflated 240-byte payload begins with schema class
`DocumentStorageIndexImpl`. Its `m_streamRevisions` contains eleven signed
32-bit revisions at schema-proven offsets 156–199, in this order:
preview, global, history, elemTable, contentDocuments, partitionTable,
incrementTable, basicFileInfo, transmissionData, partAtom and projectXMLInfo.
Every one matches the last DocumentIncrementTable entry in all six fixtures.
The final wrapper int32 immediately before gzip equals the Formats revision in
all six fixtures; Formats is absent from the nested revision structure.

The embedded-schema root decoder ends at byte 212. The remaining 28 bytes are
preserved as opaque bytes, not represented as decoded root fields.
`patch_contents_payload` binds evidence to source SHA-256, checks unique field
spans and original values, changes only requested revision bytes, and rebuilds
gzip CRC/ISIZE. The caller applies the normal page encoder. Identity patches
return byte-identical logical streams. Revision-only trials across all six
fixtures independently decode to exactly the requested changed fields.

## BasicFileInfo and History identity

All six fixtures satisfy these equalities:

- `Unique Document Increments` and the central model's last-reload version
  equal the increment-array length and final `m_majorVersion`.
- `Unique Document GUID` and the central model's last-reload episode GUID
  equal the first, newest History episode GUID (UUID little-endian bytes).
- That GUID matches none of History's five top-level GUID fields.

Thus preserving BasicFileInfo while appending an increment and prepending a
History episode leaves demonstrably inconsistent counters and episode identity.
The public reader describes document identity as stable across saves; this
cross-stream evidence does not establish that interpretation, and the patcher
uses the observed newest-episode relationship explicitly.

`patch_basic_file_info(source, evidence, increments, document_guid=None)` checks
source SHA-256, exact UTF-16 property spans, labels and CRLF terminators. It
updates both counters and, when supplied, both textual GUIDs, preserving every
other byte. Counter edits must retain digit width; 85 to 86 is supported, 99 to
100 fails rather than inventing binary framing. Six independent reader trials
verify both counters and GUIDs change as requested while all other parsed
properties remain equal. Binary fields are preserved, not claimed understood.

## Global/Latest follow-up

The embedded-schema graph decoder consumes all of each `Global/Latest` payload
after separating its final four zero closing bytes. Graphs contain 252, 212,
457, 236, 264 and 242 objects respectively (1,663 total). This establishes full
wire traversal for these fixtures, not complete understanding of field meaning.
The ADocument root's `m_pHistory` token is null in all six.

Top-level graph fields whose names contain GUID, increment, episode, sequence,
counter, version or history identify SteelModelInfo and GlobalParamTracking.
Their increment counts and relevant GUIDs are zero or empty in every fixture;
no additional nonzero duplicate save counter was established. The compact
report includes those values and exact object offsets. This name-based filter
does not rule out references with other names or deeper inline fields.

## Reproduction and limits

```sh
python3 research/rvt/save_identity.py --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --target research/rvt/local/schema-target research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt research/rvt/local/RE1-Architecture.rvt research/rvt/local/RE1-Electrical.rvt research/rvt/local/RE1-Mechanical.rvt research/rvt/local/RE1-Plumbing.rvt > research/rvt/results/save-identity.json
python3 -m unittest discover -s research/rvt -p test_save_identity.py
```

Six focused tests cover exact preservation, revision spans, hashes, unknown
fields, malformed spans, integer bounds, fixed-width counter
changes and paired GUID updates. Satisfying these relationships does not prove a
complete Revit save: signature generation and transaction allocation semantics
remain unproven, and no Autodesk acceptance result is available.
