# Project element tables and partition membership

`element_table.py` decodes and re-encodes the observed 28-byte (2023) and
40-byte (2024/2025) project records. It preserves opaque fields, validates
strict ID ordering and owner membership, rejects owner cycles, and checks the
trailing ID ceiling. Owner traversal is iterative, including a 5,000-node test.
These are constraints observed in this corpus, not a universal format claim.

The file-embedded schemas identify the trailer class as `IdentifierSource`,
with field `m_last`. Its tags are 2261, 2305 and 2363 for the tested versions.
This does not prove that allocating `m_last + 1` alone is sufficient or safe.
`schema_probe.py` checks those tags using the pinned public clean-room reader.

Reproduce the byte-identity, History episode-range, owner graph and object-ID
joins (after fetching the licensed fixtures):

```sh
python3 research/rvt/verify_element_tables.py \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-*.rvt
```

All 53,544 table records round-trip byte-for-byte. Every owner reference
resolves, owner graphs are acyclic, and every episode number is within its
History list. There are 2,245 base-group IDs absent from project tables.

The machine-readable results are in `element-tables.json`. Every project table
ID occurs in a base partition group. GUID-keyed content groups contain no IDs
from the project table in these six files. Some base groups contain IDs absent
from the table; the audit reports these without assuming they are deleted or
live elements. Project IDs and content-group IDs must not be conflated when
building a writer.

This codec does not implement element allocation, class-specific bodies,
reference repair, signature generation, or a complete Revit save. Autodesk
acceptance of modified files remains untested.
