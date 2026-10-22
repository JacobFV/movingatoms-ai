# Append-save research candidate and omission controls

The latest candidate, `save-candidate-v5.rvt`, appends a changed existing room in
`Partitions/85`, adds History episode 703, updates the room's last modification
episode, and appends an increment to both increment arrays. Contents revisions
match the latest increment; BasicFileInfo counters report 86 and its two document
GUID strings match the new newest History episode. All four known counter copies and four GUID copies in BasicFileInfo agree.
Reverse-editing those fields reproduces the original stream exactly, preserving
all remaining opaque bytes. The atomic writer preserves
all untouched streams and regenerates page parity, including Contents.

The pinned independent reader selects the room from **Partitions/85**, preserving
its creation-based UniqueId and derived IFC GUID. Its complete 11-object graph
changes only the floor finish from Wood to Polished concrete and 26 bytes of
cursor displacement. Legacy element JSON retains all 154 elements, with only that
property and the moved room's source-location provenance changed. IFC exposes a projection stability regression: **860 generated identifiers change**
when the document GUID changes. Every such line differs only in its first 22-character
IFC GUID; the remaining two changed lines are FloorCovering and SourceStream.
The verifier reports this churn explicitly rather than treating exports as stable.
Our explicit persistent-namespace adapter eliminates all 860 generated-ID changes
without touching native IDs or RVT bytes; see `ifc-identity-audit-v5.json`.
Room native identity and its derived IFC GUID remain unchanged.

## Why five candidates are retained

Parallel schema audits caught omissions the element reader did not catch. Every
candidate is preserved with its own hash; none was overwritten. The identity
audit records the relationships explicitly in `save-candidate-identity.json`.

| Candidate | Contents | BFI text counters | BFI text GUID | Binary identity copies |
| --- | --- | --- | --- | --- |
| initial | stale | stale | stale | old values |
| v2 | synchronized | stale | stale | old values |
| v3 | synchronized | synchronized | stale | stale counter |
| v4 | synchronized | synchronized | synchronized | stale counter/GUIDs |
| v5 | synchronized | synchronized | synchronized | synchronized |


The individual `save-candidate[-vN]-writer.json` files record exact output hashes
and stream verification. `save-candidate[-vN]-verification.json` records native
route, full graph, identity, element and IFC checks. Earlier candidates are
negative bookkeeping controls, despite their successful element projections.

## Subsequent binary-header finding

The seven checks above cover the decoded Contents revisions and textual
BasicFileInfo properties. A subsequent audit found binary-prefix copies of the
BasicFileInfo counter and two GUIDs; v4 leaves those stale. The structural codec and v5 candidate now synchronize these copies and
the additional framed decimal counter. The separate binary identity check records
the failure for v3/v4 and success for v5.

## Unresolved validity

This is **not a complete or Autodesk-validated save algorithm**. Generation
requires `--acknowledge-hypotheses`. Old record retention, unchanged user-modification
episode, unsigned partition acceptance, and complete save semantics are not
established. The new partition has empty signature fields, explicitly experimental.
Ancillary contentDocuments/transmissionData/projectXMLInfo revisions remain
unchanged although historical saves in this corpus advanced them. Advancing
numbers without understanding associated stream changes would not establish
correctness. Other BasicFileInfo binary fields remain opaque and byte-preserved.
No new element class or geometry has been created.

## Reproduction

Use the licensed pinned Architecture fixture and a clean pinned public rvt-rs
checkout. Destinations must not exist. Build the current Rust writer: earlier
binaries may not support partition creation or Contents page framing.

```sh
python3 research/rvt/save_candidate.py research/rvt/local/RE1-Architecture.rvt \
  research/rvt/local/save-candidate-v5 --acknowledge-hypotheses \
  --contents-evidence research/rvt/results/save-identity.json \
  --update-basic-file-info --update-document-guid --synchronize-binary-identity \
  > research/rvt/results/save-candidate-v5-plan.json
cargo build --release --manifest-path processing/rvt-native/Cargo.toml
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v5.rvt \
  research/rvt/local/save-candidate-v5/manifest.json \
  > research/rvt/results/save-candidate-v5-writer.json
python3 research/rvt/current_record_probe.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target --element 348738 \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v5.rvt \
  > research/rvt/local/save-candidate-v5-native.json
research/rvt/local/rvt-elements research/rvt/local/save-candidate-v5.rvt \
  > research/rvt/local/save-candidate-v5-elements.json
research/rvt/local/rvt-ifc research/rvt/local/save-candidate-v5.rvt \
  -o research/rvt/local/save-candidate-v5.ifc
python3 research/rvt/save_candidate_verify.py research/rvt/local --stem save-candidate-v5
python3 research/rvt/save_identity.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/save-candidate*.rvt \
  > research/rvt/local/save-candidate-identity.json
python3 research/rvt/save_candidate_identity_verify.py research/rvt/local
python3 -m unittest discover -s research/rvt -p test_save_candidate.py
```

The verifier also uses `architecture-elements.json` and
`architecture-original.ifc`, generated from the unchanged source fixture.
Native evidence is bound to both actual file hashes and the pinned reader commit.
Full graphs and binaries remain in ignored local storage; reports retain hashes.
To reproduce earlier controls, omit `--synchronize-binary-identity` for v4;
also omit `--update-document-guid` for v3; omit both BFI flags for v2; omit
all synchronization flags for initial. Structural validation of binary copies
is a byte-level check; the independent public reader verifies the text/schema
relationships and current native record, not undocumented binary semantics.
