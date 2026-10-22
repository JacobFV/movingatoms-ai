# Save increment table codec

`save_increments.py` now decodes and encodes the complete inflated
`Global/DocumentIncrementTable` payload for the observed Revit 2023, 2024 and
2025 profiles. Its field names and ordering come from each file's embedded
schema, independently decoded by the pinned public clean-room reader
`b6086d41b9758fd9b92f42f0a47b8345b9c58056`. No proprietary implementation was inspected.

The codec covers both increment arrays, redirect/version records, UTF-16
user and comment strings, greatest episode, episode count, timestamp words,
major version, object count, all twelve stream revisions, overwrite flags,
empty permutation arrays and the four-byte closing marker. It rejects unknown
profiles, truncated or oversized arrays, invalid boolean bytes, unexpected
closing data and unknown encoder fields.

All six licensed fixtures reproduce byte-for-byte (125,144 inflated bytes).
Every decoded field equals the independent schema decoder's output. The
arrays contain 422 increments and 422 local increments; the two arrays are
identical in each fixture. The implementation preserves their independence:
this observation is not a requirement that future states keep them equal.
All observed permutation arrays are empty. Nonempty permutations are explicitly
rejected on both decode and encode. The pinned public reader's
`native_index.rs::qualify_single_increment_permutation` expects structured pairs
(`first.m_id`, `second`), so a flat integer layout would be unjustified. No
nonempty wire layout or routing semantics are claimed from this corpus.

This is a concrete serialization prerequisite for save transactions. It does
**not** establish which stream revisions should advance, how timestamps relate
to transaction identity, or when compaction/version records should be appended.
No complete save transaction or Autodesk acceptance is claimed. Raw source
user/comment strings stay in ignored local evidence; the committed report
contains only structural counts and hashes.

Reproduce:

```sh
python3 research/rvt/bookkeeping_probe.py \
  --reader-source /path/to/pinned/rvt-rs --target research/rvt/local/schema-target \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-*.rvt > research/rvt/local/bookkeeping.json
python3 research/rvt/save_increment_audit.py \
  research/rvt/local/bookkeeping.json research/rvt/local \
  > research/rvt/results/save-increments.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_save_increments.py -v
```

Five tests cover all supported tags, Unicode and embedded NUL strings,
independent arrays, revision editing, every byte truncation, trailing data,
invalid flags, unknown fields, integer overflow and explicit rejection of
nonempty permutations. Screenshot evidence should
show these command outputs or the report, and must not imply a Revit UI run.
