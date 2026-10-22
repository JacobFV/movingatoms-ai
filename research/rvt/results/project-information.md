# Guarded ProjectInformation timestamp update

`project_information_codec.patch_timestamp` updates only the two observed XML
`updated` values inside ProjectInformation's single-entry ZIP. It verifies the
source SHA-256, ZIP directory layout, matching local/central CRC and lengths,
deflate EOF, and XML timestamp structure. It requires one Atom updated node and
one Autodesk design-file updated node, with the same fixed-width timestamp.

The caller supplies the source and proposed increment timestamps, whose high
words must be zero. The patcher derives the difference between the source
increment timestamp and the source XML timestamp. The original six licensed
fixtures exhibit two offsets:

| Sources | Observed offset |
|---|---:|
| Core Interior, Einhoven | 14,400 seconds |
| RE1 Architecture, Electrical, Mechanical, Plumbing | 36,000 seconds |

Only these observed offsets are enabled. Unknown offsets fail explicitly.
Preserving the source offset for a new save is recorded as a hypothesis; the
code does not pretend to resolve timezone or daylight-saving policy from the
literal `Z` suffix.

The XML bytes are changed only at the two uniquely validated timestamp values.
ZIP filenames, timestamps, flags, extra fields, comments, attributes and all
other metadata are copied as raw bytes. Only CRC, compressed/uncompressed
sizes and the central directory offset are regenerated. Gzip/page framing is
not applied to this nonpaged ZIP stream. Identity updates return the original
ZIP bytes exactly.

The eleven-fixture audit tests the six original files plus all five historical
Core snapshots. A 60-second update succeeds in all eleven: independent Python
ZIP reading checks CRC, and every ZIP metadata field outside the required
CRC/size changes remains equal. Three focused tests cover both offsets,
identity output, metadata preservation, exact XML changes, stale source hashes,
unsupported times/offsets, ambiguous timestamps and malformed ZIP structures.

```sh
python3 research/rvt/project_information_audit.py research/rvt/local > research/rvt/results/project-information.json
python3 -m unittest discover -s research/rvt -p test_project_information_codec.py
```

This is a supported structural edit for the observed ZIP layout. It neither
proves a universal save-time policy nor establishes Autodesk acceptance.
