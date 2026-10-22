# Historical native-record and modification-history transitions

Six licensed historical snapshots now provide before/after evidence instead of
only unrelated static distributions. Source commits, hashes, MIT provenance and
retrieval are documented separately in [paired-save-sources.json](paired-save-sources.json).
The tool requires every later History to preserve the earlier episodes as an
exact suffix, so episode numbers retain their meaning across each comparison.
These are adjacent Git snapshots, **not controlled or necessarily adjacent
Revit saves**. The source commit messages do not establish every user operation.

All five pairs complete with strict page parity, partition framing, object
lengths/checksums and conservative current-record selection. Every shared ID
retains its native UniqueId, and no shared record selection is unresolved.
The first two snapshots use exact episode routing for every project record;
the remaining four each have ten selections through unique compaction-history
holders, which are explicitly counted in the JSON. No highest-stream fallback
is used. Only project/base groups are compared; embedded content namespaces
are not conflated with project IDs.

## What actually changed

Body comparisons hash each complete inflated native object body independently
in channels 101, 102 and 103. A changed hash establishes different serialized
bytes, not a particular semantic edit.

| Earlier → later commit prefix | Shared IDs | Added / removed IDs | Changed native bodies | Changed bodies, user date unchanged | Unchanged bodies, modification date advanced |
| --- | ---: | ---: | ---: | ---: | ---: |
| bd8c0792 → 21b61e69 | 20,028 | 13,342 / 128 | 254 | 114 | 16 |
| 21b61e69 → 5859762b | 26,702 | 122 / 6,668 | 244 | 244 | 22 |
| 5859762b → ede6e635 | 26,759 | 41 / 65 | 27 | 12 | 2 |
| ede6e635 → 8946a8ca | 26,764 | 35 / 36 | 572 | 353 | 39 |
| 8946a8ca → fd755e18 | 26,407 | 18 / 392 | 16 | 13 | 1 |

A native body change therefore does **not** universally imply that the user
modification episode advances. This rules out that blanket rule. It does not
establish whether an explicitly user-requested room finish edit should update
that field: regeneration, deletion, cleanup, view changes and other operations
are not isolated in these snapshots. The room candidate's specific rule still
needs to be labeled a hypothesis.

The converse also fails: some modification episodes advance without any change
to the selected bodies in all three channels. The full transition matrix,
including which channels changed and before/after episode triples, is in
[paired-modification.json](paired-modification.json). Examples are capped at ten
per matrix category; counts include every comparable project ID.

Three channel-101 changes occur while both modification dates stay unchanged:

- Elements 58253 and 108205 between 21b61e69 and 5859762b, both selected from
  physical increment 48 before and after, with exact episode routes.
- Element 130252 between ede6e635 and 8946a8ca, selected from increment 53 in
  both files, also with exact routes.

[Header details](paired-modification-header-details.json) preserve exact body
hashes and changed offsets. Elements 58253 and 130252 each change only byte 60
from 1 to 0 (239-byte and 215-byte bodies respectively). Element 108205 shrinks
from 53,375 to 53,367 bytes, with byte 74 changing 2 to 1 and tail changes. The
semantic cause is not asserted. These cases are not artifacts of choosing a
different physical holder.

## Ancillary revision observations

| Pair | History episodes | Increment entries | Regular stream revision |
| --- | --- | --- | --- |
| bd8c0792 → 21b61e69 | 31 → 33 | 48 → 51 | 47 → 50 |
| 21b61e69 → 5859762b | 33 → 34 | 51 → 53 | 50 → 52 |
| 5859762b → ede6e635 | 34 → 36 | 53 → 59 | 52 → 58 |
| ede6e635 → 8946a8ca | 36 → 37 | 59 → 61 | 58 → 60 |
| 8946a8ca → fd755e18 | 37 → 39 | 61 → 66 | 60 → 65 |

Here “regular” means the latest increment's preview, global, History, ElemTable,
ContentDocuments, PartitionTable, increment-table, BasicFileInfo,
TransmissionData and ProjectXMLInfo revision fields, which all share the value
shown in these snapshots. Formats stays 10 and PartAtom stays -1. Thus increment
and stream revision growth is not one-for-one with History episode growth.
This supports keeping those counters distinct; it does not prove the exact
single-save allocation rule for a different document.

## Reproduction

Run the separately documented source downloader/provenance audit first. Then:

```sh
python3 research/rvt/paired_modification_corpus.py \
  research/rvt/results/paired-save-sources.json research/rvt/local \
  > research/rvt/results/paired-modification.json
python3 research/rvt/paired_modification_details.py \
  research/rvt/results/paired-modification.json research/rvt/local \
  > research/rvt/results/paired-modification-header-details.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_paired_modification.py -v
```

`paired_modification.py` also accepts a single pair with required SHA-256
arguments. Four tests cover distinct body/revision transitions, identity reuse,
unresolved records, sentinel transitions, added/removed IDs and rejection of
unrelated/reordered History lineage. Historical fixtures exposed overly strict
page-layout selection; the corrected codec verifies the original layout and
parity rather than bypassing either. No modified RVT files are emitted by these
audits, and no Autodesk acceptance is claimed.
