# Guarded three-wall append plan

`wall_batch_candidate.py` builds one unpublished patch manifest containing three independently schema-encoded walls. It validates the entire request and constructs all payloads before creating the destination. It does not modify or publish an existing candidate.

The demonstration uses IDs 133210–133212 in creation episode 39, with one new `Partitions/66` stream:

| Element | Length (feet) | XY translation (feet) |
| --- | ---: | --- |
| 133210 | 6 | 400, 0 |
| 133211 | 12 | 430, 0 |
| 133212 | 18 | 470, 0 |

Every wall retains the measured type, levels, phase, material, 2/3-foot thickness and 15-foot height. Their saved bounds are disjoint and more than one foot east of every source saved header bound. The source-bounds claim covers saved header boxes, not regenerated geometry.

The allocator appends three rows while using the same original history for each allocation, then appends one history episode. Both increment arrays have object counts of three in the row and its version entry. The structural wall registration receives all three IDs in one source-hash-bound splice. Contents, BasicFileInfo and ProjectInformation use the existing coordinated save metadata routines. The deterministic episode GUID includes the normalized request, so different requests do not reuse that episode identity.

[The plan](wall-batch-plan.json) records individual geometry audits and body hashes, new identifiers, the preserved old table rows, registration change, partition hash and acknowledged hypotheses. Independent whole-file verification is separate from this builder report.

Five focused tests cover three different walls, invalid/nonfinite/duplicate requests, source and new-wall overlap rejection, exact batch registration bytes, and no output directory on rejected requests. The generated increment payload was decoded to confirm both count fields in both arrays equal three.

```sh
python3 -m unittest discover -s research/rvt -p test_wall_batch_candidate.py
python3 research/rvt/wall_batch_candidate.py \
  research/rvt/local/core2024.rvt research/rvt/local/new-batch-patches \
  --acknowledge-hypotheses
```

Use `--specs path.json` for a JSON list of objects containing exactly `length_feet` and `translation_xy` (two finite feet values). Limits are 1–100 walls, length 0.01–10,000 feet, and translation components at most 100,000 feet in magnitude. Existing destination directories are rejected.

Unsigned acceptance, complete native save lifecycle, and the effect of the non-room-bounding flags remain hypotheses. This experiment does not establish production native export or acceptance by Autodesk software.
