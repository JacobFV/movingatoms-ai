# Minimal project save context

The pinned `minimal_seed-Project.rvt` supports exact round trips through existing History, increment-table, element-table and BasicFileInfo codecs. Complete Global decoding consumes 825,738 bytes in 208 objects. The measured context and an explicitly hypothetical one-element append plan are in [seed_save_context.json](seed_save_context.json).

The first fresh ID is **2746**, derived from the stored allocator ceiling 2745; the maximum live element ID is only 2374 and must not be used as the allocator. The next History episode is 1, proposed append partition ordinal is 1, and next increment major version / BasicFileInfo counter is 2. All existing stream revision fields are zero except absent PartAtom (-1). The initial increment has `overwrite=true`; the append helper proposes `false`, following the existing append hypothesis rather than seed-specific paired-save evidence.

Contents uses gzip offset 91. Its independently decoded stream revisions match the latest increment and its Formats wrapper revision is zero. The report includes exact source-bound Contents bytes, field spans and hashes compatible with `save_identity.patch_contents_payload`. BasicFileInfo's four identity copies match the newest episode and single increment.

Two Core-specific assumptions must change explicitly:

- `StructuralElemSetTracking` exists but has an empty ID set. The old registration helper requires donor wall 20826 in that set and must continue rejecting this source. First-wall registration needs a separate seed-bound empty-set policy; the schema-decoded tracker and byte boundaries are recorded.
- ProjectInformation's XML timestamp is **10,800 seconds** behind its increment timestamp. The current guarded patcher accepts only the previously measured 14,400/36,000 offsets and correctly refuses this fixture. This new observation supports a seed-specific offset guard; preserving the offset is still a save-policy hypothesis, not a timezone algorithm.

The reusable `allocation_plan(table, history, fields, count, timestamp, guid)` validates count/episode/timestamp, uses the stored allocator, and gives every new row the same pending episode. It sets both increment arrays' total-element and increment-version counts to the batch size. It does not write a candidate or claim that missing wall dependencies have been resolved. The report removes decoded actor strings.

Six tests pass (including registration byte preservation and timestamp source guards): allocator ceiling and batch counts, invalid counts, inconsistent episode state, and non-increasing timestamps. Reproduce:

```sh
python3 research/rvt/seed_save_context.py research/rvt/local/minimal_seed-Project.rvt \
  --probe research/rvt/local/new-element-build/target/release/rvt-new-element-probe \
  --identity-probe research/rvt/local/schema-target/release/rvt-save-identity-probe \
  --result research/rvt/results/seed_save_context.json
python3 -m unittest discover -s research/rvt -p test_seed_save_context.py
```

Unresolved dependencies include wall type/material/style mapping and the seed's missing second level. No source or candidate file was modified. Partition allocation, initial structural registration, ancillary revisions, unsigned acceptance and native application regeneration remain experimental policies.

## Guarded integration helpers

`register_seed(raw, report["registration_evidence"], wall_ids, level_ids)` inserts walls into the measured empty structural set and new levels into both `DatumTracking` and `ElementTrackingData` category -2000240. Authoritative field spans come from the new public-reader `seed_save_context.rs` probe. The category-array container is explicitly selected because earlier symbol arrays also contain ID sets. A trial with level2746 and walls2747/2748 independently decodes completely and differs semantically in exactly those three fields; all other bytes are preserved.

No plan-view association is invented: Core has74 actual Levels but only15 `LevelPlanViewTracking` keys, so an empty map entry is not universally required by the observed files. Preserving that map for the new no-view level remains a stated policy hypothesis.

`patch_seed_timestamp(zip, old_timestamp, new_timestamp)` requires the exact seed ZIP SHA and measured10800-second offset. It preserves all XML bytes other than the two timestamps, ZIP metadata except required size/CRC/central-offset updates, and returns exact original bytes for a no-op. It does not relax the shared general timestamp codec.

The independent tracker probe is built from `seed_save_context.rs` with the same pinned public reader and serde_json1.0.154 as the other research probes; its executable is `local/schema-target/release/rvt-seed-save-context`. The audit expects this executable, alongside the existing independently built Global/Contents probes. No donor or seed model file is mutated by these measurements.

## Contents trailing-byte variant

Unlike the earlier six-file corpus, this seed's logical Contents stream has exactly one `00` byte after its gzip member. The shared strict Contents patcher correctly rejects this variant. `patch_seed_contents(logical, evidence, revisions)` pins the complete original logical SHA, requires precisely that measured suffix, passes the gzip-only prefix to the unchanged strict codec with an adjusted source hash, then restores and verifies the suffix. A no-op returns byte-identical input; missing, nonzero, doubled, and mismatched-evidence suffixes are rejected.

Seven tests now pass. Independent public-reader decoding of a five-revision trial matches the expected entire `DocumentStorageIndexImpl` field tree exactly, and the final zero remains present. This supports only the measured seed wrapper variant; it does not broaden the shared codec or establish that the final zero is optional.
