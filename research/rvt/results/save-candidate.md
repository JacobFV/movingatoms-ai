# Append-save research candidate and omission controls

The latest candidate, `save-candidate-v4.rvt`, appends a changed existing room in
`Partitions/85`, adds History episode 703, updates the room's last modification
episode, and appends an increment to both increment arrays. Contents revisions
match the latest increment; BasicFileInfo counters report 86 and its two document
GUID strings match the new newest History episode. The atomic writer preserves
all untouched streams and regenerates page parity, including Contents.

The pinned independent reader selects the room from **Partitions/85**, preserving
its creation-based UniqueId and derived IFC GUID. Its complete 11-object graph
changes only the floor finish from Wood to Polished concrete and 26 bytes of
cursor displacement. Legacy element JSON retains all 154 elements, with only that
property and the moved room's source-location provenance changed. IFC exposes a projection stability regression: **860 generated identifiers change**
when the document GUID changes. Every such line differs only in its first 22-character
IFC GUID; the remaining two changed lines are FloorCovering and SourceStream.
The verifier reports this churn explicitly rather than treating exports as stable.
Room native identity and its derived IFC GUID remain unchanged.

## Why there are four controls

Parallel schema audits caught omissions the element reader did not catch. Every
candidate is preserved with its own hash; none was overwritten. The identity
audit records the relationships explicitly in `save-candidate-identity.json`.

| Candidate | Contents revisions | BFI counters | BFI newest-episode GUID |
| --- | --- | --- | --- |
| initial | stale | stale | stale |
| v2 | synchronized | stale | stale |
| v3 | synchronized | synchronized | stale |
| v4 | synchronized | synchronized | synchronized |

The individual `save-candidate[-vN]-writer.json` files record exact output hashes
and stream verification. `save-candidate[-vN]-verification.json` records native
route, full graph, identity, element and IFC checks. Earlier candidates are
negative bookkeeping controls, despite their successful element projections.

## Subsequent binary-header finding

The seven checks above cover the decoded Contents revisions and textual
BasicFileInfo properties. A subsequent audit found binary-prefix copies of the
BasicFileInfo counter and two GUIDs; v4 leaves those stale. A codec and further
candidate are in progress. The passing seven checks do not cover this newly
identified inconsistency.

## Unresolved validity

This is **not a complete or Autodesk-validated save algorithm**. Generation
requires `--acknowledge-hypotheses`. Old record retention, unchanged user-modification
episode, unsigned partition acceptance, and complete save semantics are not
established. The new partition has empty signature fields, explicitly experimental.
Ancillary contentDocuments/transmissionData/projectXMLInfo revisions remain
unchanged although historical saves in this corpus advanced them. Advancing
numbers without understanding associated stream changes would not establish
correctness. BasicFileInfo binary fields remain opaque and byte-preserved.
No new element class or geometry has been created.

## Reproduction

Use the licensed pinned Architecture fixture and a clean pinned public rvt-rs
checkout. Destinations must not exist. Build the current Rust writer: earlier
binaries may not support partition creation or Contents page framing.

```sh
python3 research/rvt/save_candidate.py research/rvt/local/RE1-Architecture.rvt \
  research/rvt/local/save-candidate-v4 --acknowledge-hypotheses \
  --contents-evidence research/rvt/results/save-identity.json \
  --update-basic-file-info --update-document-guid \
  > research/rvt/results/save-candidate-v4-plan.json
cargo build --release --manifest-path processing/rvt-native/Cargo.toml
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v4.rvt \
  research/rvt/local/save-candidate-v4/manifest.json \
  > research/rvt/results/save-candidate-v4-writer.json
python3 research/rvt/current_record_probe.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target --element 348738 \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v4.rvt \
  > research/rvt/local/save-candidate-v4-native.json
research/rvt/local/rvt-elements research/rvt/local/save-candidate-v4.rvt \
  > research/rvt/local/save-candidate-v4-elements.json
research/rvt/local/rvt-ifc research/rvt/local/save-candidate-v4.rvt \
  -o research/rvt/local/save-candidate-v4.ifc
python3 research/rvt/save_candidate_verify.py research/rvt/local --stem save-candidate-v4
python3 research/rvt/save_identity.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/save-candidate*.rvt \
  > research/rvt/local/save-candidate-identity.json
python3 -m unittest discover -s research/rvt -p test_save_candidate.py
```

The verifier also uses `architecture-elements.json` and
`architecture-original.ifc`, generated from the unchanged source fixture.
Native evidence is bound to both actual file hashes and the pinned reader commit.
Full graphs and binaries remain in ignored local storage; reports retain hashes.
To reproduce earlier controls, omit both BFI flags for v2; omit only
`--update-document-guid` for v3; omit all three synchronization flags for initial.
