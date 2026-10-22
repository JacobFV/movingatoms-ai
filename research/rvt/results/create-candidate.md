# Fresh DataStorage append and registration experiment

`create-candidate-ancillary.rvt` contains a newly encoded DataStorage with ID
133210, episode 39 and new physical partition 66. Its name is
`Clean-room DataStorage Δ`; its fresh Extensible Storage identity GUID is
`7cd7ab1f-7535-5cd6-a873-a3af417c6e4d`. It uses two existing file-local ES schemas.
This is a bounded non-geometric element experiment, not a general element writer.

Independent native-reader checks establish:

- All 26,425 prior native identities are unchanged; the new identity is derived
  from the new creation episode. All original partition streams remain byte-identical.
- All three new object channels route exactly to Partitions/66 and decode complete
  graphs. Their body hashes match the independently checked schema encoder.
- Outgoing element references are self or unset; the new storage GUID is absent
  from every current DataStorage GUID enumerated in the source.
- Three incoming registrations are added to Global/Latest: the `-100` cell-tracking
  set and the two associated ES-schema tracking sets. Independent complete decoding
  preserves all 252 objects and 251 edges, with only those three ID insertions.
  The actual candidate's inflated Global/Latest hash is bound to that graph audit.
- Contents revisions, increment arrays, History and all known binary/text
  BasicFileInfo identity copies agree. Reversing BFI identity edits recovers the
  original bytes, preserving opaque fields.

The initial `create-candidate.rvt` deliberately lacks those three registrations.
It remains as a negative control: a successful native element decode alone did
not establish document registration. Both controls have separate hashes and reports.

Default IFC export changes 13,830 generated identifiers because its namespace uses
the new save GUID. Our explicit persistent namespace adapter yields a byte-identical
IFC export. DataStorage has no IFC geometry projection; unchanged IFC is therefore
an expected projection result, not proof of complete native save validity.

The ancillary follow-up additionally advances contentDocuments, transmissionData
and projectXMLInfo revision counters and updates two ProjectInformation timestamps.
Exactly three streams differ from the preserved registered control: ProjectInformation,
Contents and DocumentIncrementTable. See `ancillary-candidates.md`.

## Limits

Signatures are explicitly empty in the new partition. Their acceptance is unknown.
The three measured registrations are consistent, but all possible incoming
registration requirements and complete Revit save behavior are not proven.
Retained preview revision/content and old-record retention remain save-policy
hypotheses. No Autodesk acceptance result exists. This experiment does not create
walls, families, geometry, or a production-ready native project from scratch.

## Reproduction

Use the pinned MIT core2024 fixture, current rebuilt Rust writer and clean pinned
public reader. Output directories/files must not exist.

```sh
python3 research/rvt/create_candidate.py research/rvt/local/core2024.rvt \
  research/rvt/local/create-candidate-registered --acknowledge-hypotheses \
  --registration-evidence research/rvt/results/new-element-registration.json \
  > research/rvt/results/create-candidate-registered-plan.json
cargo build --release --manifest-path processing/rvt-native/Cargo.toml
processing/rvt-native/target/release/ma-rvt-native patch research/rvt/local/core2024.rvt \
  research/rvt/local/create-candidate-registered.rvt \
  research/rvt/local/create-candidate-registered/manifest.json \
  > research/rvt/results/create-candidate-registered-writer.json
python3 research/rvt/create_candidate_verify.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/core2024.rvt \
  research/rvt/local/create-candidate-registered.rvt \
  > research/rvt/results/create-candidate-registered-verification.json
python3 research/rvt/save_identity.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/create-candidate-registered.rvt \
  > research/rvt/local/create-candidate-registered-identity.json
python3 research/rvt/create_candidate_projection.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/core2024.rvt \
  research/rvt/local/create-candidate-registered.rvt research/rvt/local/create-candidate-registered-ifc \
  > research/rvt/results/create-candidate-registered-projection.json
python3 -m unittest discover -s research/rvt -p test_create_candidate.py
```

Omit `--registration-evidence` and use fresh `create-candidate` destinations to
reproduce the unregistered control. The complete registration-graph evidence and
its own reproduction are in `new-element-registration.json` and the new-element
research scripts. Binary models and full graphs remain in ignored local storage.
