# Ancillary revisions versus paired stream bytes

Six MIT-licensed historical Core Interior snapshots provide five real file
transitions. `ancillary-transitions.json` hashes every CFB stream at stored and,
where applicable, validated unpaged logical layers. Gzip payloads are inflated
with CRC/length validation. Partition gzip member lists use length-framed hashes
to preserve member boundaries; ProjectInformation ZIP entries are independently
inflated and CRC-checked. Private ZIP entry names are hashed.

| Git transition | Latest regular revision | ContentDocuments bytes | PartitionTable bytes | TransmissionData bytes |
|---|---|---|---|---|
| bd8c0792 → 21b61e69 | 47 → 50 | Identical | Identical | Changed |
| 21b61e69 → 5859762b | 50 → 52 | Identical | Identical | Changed |
| 5859762b → ede6e635 | 52 → 58 | Identical | Identical | Changed |
| ede6e635 → 8946a8ca | 58 → 60 | Identical | Identical | Identical |
| 8946a8ca → fd755e18 | 60 → 65 | Identical | Identical | Changed |

ContentDocuments and PartitionTable are identical at **all three layers** in
all five transitions. Their stream revisions still advance by 3, 2, 6, 2 and 5,
matching increment-count deltas. TransmissionData is entirely identical in one
pair while its revision advances by two. Consequently, preserving a revision
merely because the stream bytes did not change contradicts observed behavior.

Formats is byte-identical across all six snapshots and its revision remains
10. PartAtom is absent and its revision remains -1. Preview and
ProjectInformation bytes change in every pair; these endpoints do not establish
whether a preserved preview payload should advance its revision.

## Candidate policy recommendation

For a candidate deliberately modeled on these historical increment transitions,
advancing ContentDocuments and TransmissionData revisions by one alongside the
new increment is better supported than retaining them solely because their
bytes remain unchanged. This remains an extrapolation to a new save, not a
universal Revit allocation rule. It does not require inventing content changes
to unchanged streams. Revision deltas and physical content changes must remain
separate assertions in candidate evidence.

## ProjectInformation mapping and XML follow-up

The actual CFB inventory contains `ProjectInformation`, a one-entry ZIP whose
payload root is an Atom XML `entry`; no stream named `projectXMLInfo` exists.
The pinned public reader's [project_information.rs](https://github.com/DrunkOnJava/rvt-rs/blob/b6086d41b9758fd9b92f42f0a47b8345b9c58056/src/project_information.rs) independently identifies
this stream as project XML metadata. Mapping the increment field
`m_projectXMLInfoStreamRevision` to this stream is an evidence-based inference;
no serialized stream-name binding has been demonstrated.

`ancillary-transitions-xml.json` compares XML element text and attributes across
all five pairs, reporting names and hashes rather than private values. Exactly
two text fields change: Atom `entry/updated` and Autodesk
`design-file/updated`. After replacing those timestamp values with a common
placeholder, the complete parsed XML serializations are identical across all
six snapshots. No complete leaf value equals the newest History GUID, increment
count or latest revision values.

Both updated values are equal within each snapshot. Interpreting their `Z`
suffix literally yields a value 14,400 seconds below the latest increment's
low-word timestamp in this lineage. The full original six-file audit finds
36,000-second offsets for the RE1 models, so the offset is not universal. See
`project-information.md` for the guarded source-dependent patcher.

```sh
python3 research/rvt/ancillary_transitions.py research/rvt/local > research/rvt/results/ancillary-transitions.json
python3 research/rvt/ancillary_transitions_xml.py research/rvt/local > research/rvt/results/ancillary-transitions-xml.json
```

Git-adjacent snapshots can span multiple saves. These observations establish
specific counterexamples and relationships, not Autodesk acceptance or a
complete save specification.
