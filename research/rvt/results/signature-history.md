# Signature fields across historical Core snapshots

Date: 2026-10-22. The probe checks the SHA-256 of each of six source snapshots
against [paired-save-sources.json](paired-save-sources.json), which records MIT
license provenance and repository revisions. All partition pages are decoded
strictly; decoded partition envelopes must reproduce byte-for-byte before
comparison. No proprietary executable or implementation is accessed.

[signature-history.json](signature-history.json) records 307 group occurrences
across snapshots with 48, 49, 51, 52, 53, and 54 groups respectively. There are
54 repeated complete inflated-group identities and 729 pairwise comparisons of
those identities. All 729 have matching private fields; none differ. Of these,
723 comparisons involve nonempty private fields and six involve the repeated
empty group representation.

The 53 repeated nonempty private fields each map to exactly one inflated
message, one concatenated gzip byte sequence, and one serialized member-block
byte sequence. There is no example where a retained private field accompanies
changed gzip headers, deflate bytes, or member framing. The script records
these representations separately and would report all known group-envelope
and containing-partition differences for any equal-inflation/different-footer
pair; no such pair occurred.

Eight complete partition payloads repeat across snapshots, including
`Partitions/46`, whose entire logical bytes recur in all six. Other repeated
payloads occur under `Partitions/47`, `48`, `50`, `51`, `53`, `55`, and `59`.
The empty-group inflated representation recurs in four snapshots under
`Partitions/47`, `52`, `58`, and `60`; empty private fields are not evidence
about a signing algorithm.

These observations support **retention of complete earlier partition groups**
through later saves. They do not show that signatures were regenerated from
identical messages, so they do not establish deterministic signing. Whole-file
History and save state change while retained group bytes remain unchanged,
but that does not identify which contextual state a newly generated signature
would cover. Signature generation and enforcement remain unresolved.

The practical consequence is to preserve stored bytes and opaque signatures
for untouched groups during append-style experiments. Recompressing every
retained group would introduce an unnecessary unverified change. New or edited
groups still need their own unknown integrity handling; historical retention
does not solve that problem.

## Reproduction

```sh
python3 research/rvt/test_signature_history.py
python3 research/rvt/signature_history.py \
  --sources research/rvt/results/paired-save-sources.json \
  --directory research/rvt/local \
  > research/rvt/results/signature-history.json
```

Two envelope-comparison tests pass. They check that equal inflation does not
hide gzip-header differences, and that group/context differences are reported.
Deflate comparisons are deliberately restricted to the observed gzip FLG=0
layout; unexpected optional headers stop the probe instead of being guessed.
Git-adjacent snapshots need not be adjacent Revit saves.
