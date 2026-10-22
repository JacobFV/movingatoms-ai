# Complete observed History codec and guarded episode mutation

`save_history.py` implements the entire inflated `Global/History` payload for
the observed Revit 2023–2025 profiles: root fields, five GUID fields, variable
upgrade-version array, separate newest-first episode array and closing marker.
Six source files reproduce all **21,521 bytes** exactly. All root fields and
all **1,181 episodes** (GUID plus strength) match independent embedded-schema
decoding by pinned public reader `b6086d41b9758fd9b92f42f0a47b8345b9c58056`.
No Autodesk or ODA implementation was inspected.

The old fixed-offset experiment treated offset 14 as another episode count.
The new codec distinguishes `m_nextLocalSequenceNumber` from the actual array
count and walks the variable upgrade array. Architecture has 190 upgrade
entries, moving its episode array beyond the fixed-size root; the other five
have empty arrays.

Schema integer descriptors, recorded for every fixture in `save-history.json`:

| Field | Raw descriptor | Interpretation in pinned public decoder |
| --- | --- | --- |
| `m_nextLocalSequenceNumber` | `0x00000004` | signed i32 |
| `m_subsequenceNumberDeficit` | `0x00000004` | signed i32 |
| `m_upgradeVersions` | `0x00005004` | array of signed i32 |

The signed interpretation is from `native_parameters.rs` base 4, which calls
`i32::from_le_bytes`. The codec preserves signed boundary values, but its
allocator rejects unsupported states. Counts and pointer tokens remain u32.

`prepend_episode` adds one newest-first GUID record and advances the local
sequence only when it equals the old episode count and the deficit is zero.
It rejects duplicate/zero GUIDs, unsupported pointer/inline-episode layouts,
unknown episode strengths and sequence exhaustion. Existing reverse-indexed
episode-ID-to-GUID mappings remain unchanged. The audit independently decodes
all fields and episodes after a deterministic test prepend in every fixture.
These are in-memory History edits; no modified RVT file is emitted by this audit.

**This is not a complete save transaction.** Increment revisions, element
revisions, file identity/counters, signatures and other affected streams are
not updated here. The supported episode strength is only the observed value
`0x28`; other values fail explicitly. Root pointer tokens are restricted to
0 and 1, inline episodes to an empty array, and the closing marker to four zero
bytes. No Autodesk acceptance is claimed.

Reproduce (the bookkeeping JSON supplies fixture names/hashes; the History
fields are decoded afresh by the independently built helper):

```sh
python3 research/rvt/save_history_audit.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/schema-target \
  research/rvt/local/bookkeeping.json research/rvt/local \
  > research/rvt/results/save-history.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_save_history.py -v
```

Five tests cover all profile tags, variable upgrade arrays, exact reproduction,
every byte truncation, bad closing markers, unsupported pointer/strength/inline
layouts, safe mutation, duplicate GUIDs and signed boundary values. Reports
contain structural evidence without source user/comment information. Screenshots
of these commands/report are research evidence, not Revit UI validation.
