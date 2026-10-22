# Schema-directed save bookkeeping and storage routes

The pinned public reader independently decodes `DocumentHistory`, `ElemTable`
and `DocumentIncrementTable` from each file's embedded schema. This is an audit
of serialized relationships, not an implementation of a valid save transaction.

Observed across six licensed files:

- History offset 14 is named **m_nextLocalSequenceNumber**, not a second
  episode-array count. Its value equals the separately decoded episode count
  in this corpus. The earlier experiment's equality check is valid here, but
  should not be generalized to every possible History state.
- `m_partitionId` is zero in all 53,544 project-table rows. It must not be
  substituted for the physical `Partitions/N` stream number.
- Each active storage increment's `stored_elements` equals the sum of all
  group counts in its physical partition, including embedded content.
  All 27 physical partitions satisfy this invariant.
- Increment records include per-stream revision fields, total episode and
  element counts, chronological redirect histories, timestamps, user/comment
  strings and overwrite flags. Updating History alone leaves this state
  unchanged and is not a complete save.
- Routing each row's modification episode through the increment table finds
  a matching base record for **53,527 of 53,544** project rows. The 17 exceptions
  occur in Core Interior (10), Einhoven (6), and Electrical (1). They are
  reported, not resolved by selecting the highest-numbered stream.

`increment_routing.py` adapts the pinned reader's chronological routing rules,
with explicit rejection of unsupported permutations. The upstream reader has
an additional highest-holder fallback; this audit deliberately leaves those
cases unresolved. See the upstream attribution under `licenses/`.

```sh
python3 research/rvt/bookkeeping_probe.py \
  --reader-source /path/to/pinned/rvt-rs --target research/rvt/local/schema-target \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-*.rvt > research/rvt/local/bookkeeping.json
python3 research/rvt/verify_bookkeeping.py research/rvt/local/bookkeeping.json \
  research/rvt/results/partition-objects.json
python3 research/rvt/verify_routing.py \
  --bookkeeping research/rvt/local/bookkeeping.json \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-*.rvt
python3 research/rvt/verify_route_candidates.py research/rvt/local \
  research/rvt/results/increment-routing.json
```

The raw schema probe includes source user/comment fields and many field spans;
keep it in ignored local research storage. The committed `bookkeeping.json`
contains only the selected structural evidence, counts and room identity.
`increment-routing.json` records exact matches and unresolved candidates.

`route-candidates.json` compares every candidate's complete body hash in all
three channels. Five exceptions have only one holder; ten have multiple
holders with identical bodies. Two have competing, different bodies:
Einhoven element 2846 (increments 0/3) and Electrical element 509784
(increments 114/119). Equality is not proof of the storage route, and these
two conflicting cases specifically rule out treating every duplicate as an
interchangeable copy.

## Conservative candidate selection follow-up

`select_record` adds an explicitly labeled partial-compaction selection rule:
when the episode route lacks the ID, traverse the later causing-increment
links and require a unique physical holder on that traversal. It does not
choose the greatest ordinal. This selects 12 candidates, including both
conflicting-body cases. Five exceptions have a sole physical holder; their
historical movement remains unexplained and is labeled accordingly. Multiple
reachable holders and multiple holders outside the explicit history are errors.

`record-selection.json` records 53,527 exact episode routes, 12 unique
compaction-history holders and 5 sole physical holders with unresolved history.
The latter two categories are selection evidence from static files, not an
Autodesk-validated model of save/compaction behavior.

```sh
python3 research/rvt/resolve_route_candidates.py research/rvt/local/bookkeeping.json \
  research/rvt/results/increment-routing.json research/rvt/results/partition-objects.json
```
