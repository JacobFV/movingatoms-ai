# Stream revision relationships from retained increment rows

`revision-rules.json` records a reproducible audit of 422 historical increment
entries in six SHA-256-pinned, MIT-licensed fixtures. Each fixture's local array
matches its increment array. The wire codec reproduces the inflated bytes and
agrees with the independently decoded embedded schema at public-reader commit
`b6086d41b9758fd9b92f42f0a47b8345b9c58056`.

Across all 422 rows:

- `m_majorVersion` equals the zero-based ordinal plus one.
- `m_totalEpisodes` equals `m_greatest.m_id + 1`; each last entry's total equals
  the current History episode count.
- Global, History, ElemTable and PartitionTable revisions are equal.
- Global, History, ElemTable, PartitionTable, DocumentIncrementTable,
  ContentDocuments, BasicFileInfo, TransmissionData and ProjectXMLInfo revisions
  advance by one between every adjacent retained row. Different streams can
  have different starting revisions.
- Formats advances by zero or one. Preview also advances by zero or one.
  PartAtom remains -1. None of the audited stream revision fields decreases.

| Fixture | Entries | Global minus ordinal | Last global | Last increment table | History episodes |
|---|---:|---:|---:|---:|---:|
| core2024 | 66 | 0 | 65 | 65 | 39 |
| einhoven | 7 | 0 | 6 | 6 | 6 |
| RE1-Architecture | 85 | 200 | 284 | 285 | 703 |
| RE1-Electrical | 121 | 79 | 199 | 199 | 172 |
| RE1-Mechanical | 80 | 79 | 158 | 158 | 136 |
| RE1-Plumbing | 63 | 79 | 141 | 141 | 125 |

These are counterexamples to treating a stream revision as an increment ordinal,
or assigning all streams one revision number. Architecture's increment-table
revision is one greater than global in every retained entry. Its last
ContentDocuments and TransmissionData revisions are 173, BasicFileInfo is 255,
Formats is 175, ProjectXMLInfo is 162, and Preview is 284.

This evidence does **not** establish complete save rules. Retained metadata does
not provide historical stream contents, so a revision change cannot be equated
with a stream byte change. In particular, neither preserving a revision because
an experimental edit preserves the stream bytes nor incrementing every revision
is a proven save algorithm. Overwrite, compaction, upgrade and stream-specific
allocation need paired saves or further independently testable evidence.
Experimental append-save candidates must record their extrapolation explicitly.

Reproduce from the licensed fixtures and schema evidence:

```sh
python3 research/rvt/revision_rules.py research/rvt/local/bookkeeping.json research/rvt/local > research/rvt/results/revision-rules.json
python3 -m unittest discover -s research/rvt -p test_revision_rules.py
```

Regenerate the ignored schema evidence using the command documented in
`bookkeeping.md`. Three focused tests exercise ordinal offsets, independent
stream offsets, decreasing-revision counterexamples, invalid episode ranges and
empty inputs. This audit intentionally reports counterexamples instead of
rejecting data that violates an unproven hypothesis.
