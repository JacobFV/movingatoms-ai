# Source-bound ancillary metadata follow-up

The latest room candidate (`save-candidate-v6.rvt`) and DataStorage candidate
(`create-candidate-ancillary.rvt`) update measured ancillary metadata while
preserving their preceding candidates as controls. In each case, **only three
streams differ from its preceding control**: Contents, DocumentIncrementTable,
and ProjectInformation. All native element bodies, registrations, History,
ElemTable and BasicFileInfo remain byte-identical to the checked controls.

Historical evidence invalidated the assumption that unchanged payload bytes imply
unchanged stream revisions. ContentDocuments and PartitionTable stayed byte-identical
across all five paired transitions while their revisions advanced. One pair also
kept TransmissionData byte-identical while its revision advanced. The new explicit
policy advances contentDocuments, transmissionData and projectXMLInfo by one from
the prior revision. Other save counters already advanced; offsets are preserved,
so Architecture's incrementTable revision remains one ahead of its global revision.

ProjectInformation contains two equal XML updated timestamps. The source-bound ZIP
patcher changes only those two values, preserving all other XML bytes and raw ZIP
metadata except CRC, sizes and central-directory offset. It derives the offset
between the source increment timestamp and XML timestamps, then carries that offset
forward: 36,000 seconds for Architecture and 14,400 seconds for core2024. This is
an explicit source-offset policy, not a claim about a universal timezone rule.

Both variants pass the independent Contents/History/BasicFileInfo relationships.
The room's current route/full graph/identity and the new DataStorage's three channels,
all 26,425 preserved identities, registration evidence and binary identity checks
were rerun successfully. The strict variant verifier proves the three-stream delta
and exact revision changes. Reports bind source, control and output SHA-256 hashes.

Preview remains unchanged. Historical preview bytes changed in every paired sample,
and this work does not infer how Revit regenerates them. Unsigned acceptance and
complete native-save semantics remain unresolved.

## Reproduction

Add `--synchronize-ancillary` to the existing latest-room command (all identity flags
required), using fresh `save-candidate-v6` destinations. Add it to the registered
creation command, using fresh `create-candidate-ancillary` destinations. Rebuild and
run the same atomic Rust writer. Then:

```sh
python3 research/rvt/save_identity.py --reader-source /path/to/pinned/rvt-rs \
  --target /path/to/cached-target research/rvt/local/save-candidate-v6.rvt \
  research/rvt/local/create-candidate-ancillary.rvt \
  > research/rvt/local/ancillary-candidate-identity.json
python3 research/rvt/ancillary_candidate_verify.py \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v5.rvt \
  research/rvt/local/save-candidate-v6.rvt research/rvt/local/ancillary-candidate-identity.json
python3 research/rvt/ancillary_candidate_verify.py \
  research/rvt/local/core2024.rvt research/rvt/local/create-candidate-registered.rvt \
  research/rvt/local/create-candidate-ancillary.rvt research/rvt/local/ancillary-candidate-identity.json
```

Run the existing room/full-graph and creation verifiers against the new filenames.
`ancillary-transitions.json`, `ancillary-transitions-xml.json`, and the
ProjectInformation codec audit supply the historical and structural evidence.
