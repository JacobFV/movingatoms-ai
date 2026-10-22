# SignatureMarker structure and coverage experiment

Date: 2026-10-22. Sources: the six MIT-licensed fixtures whose complete SHA-256
identities are recorded in [signature-analysis.json](signature-analysis.json).
The probe reads only file bytes through the existing strict partition/page
codecs. It does not access Autodesk binaries, a proprietary SDK, or a server.

## Measured results

Across 523 content groups, 521 private-signature fields contain 64 bytes and two
are empty. Both empty cases are base groups with zero declared elements:
`einhoven.rvt / Partitions/6` and `RE1-Electrical.rvt / Partitions/120`.
They still contain three gzip members holding terminal records. **This corpus
provides no example of a nonempty element group with an empty signature.**

The standard raw Ed25519 interpretation `R[32] || S[32]` requires the
little-endian scalar `S` to be below the Ed25519 subgroup order. Only 41 of 521
fields meet that necessary condition; 480 do not. Thus standard canonical raw
Ed25519 cannot explain all these fields in that byte layout. This does not
exclude a transformed or differently encoded value. The scalar requirement is
specified in [RFC 8032, section 5.1.7](https://www.rfc-editor.org/rfc/rfc8032#section-5.1.7).

Interpreting the halves as big-endian P-256 `r` and `s`, all 521 fall in the
scalar range; 255 have `s` in the lower half of the range. This is **not evidence
identifying ECDSA**: almost all random 64-byte values satisfy the range check.
The low-half result rules out a universal low-`s` normalization requirement for
that exact interpretation. No public key or verification equation was tested.

No byte position is constant, no halves are identical, no full footer repeats,
and no complete inflated group repeats in the nonempty-signature corpus.
Therefore these fixtures do not supply a repeated-message experiment that
could establish determinism or distinguish signed message coverage.

There are zero matches in 56,268 comparisons against SHA-512, SHA3-512, and
BLAKE2b-512, each checked forward and byte-reversed, for these explicit inputs:

- Concatenated inflated members, concatenated complete gzip frames, and
  concatenated serialized member headers + frames + checkbacks.
- Inflated data for each sequence (101, 102, 103) separately.
- Each preceding input with little-endian group count followed by the raw
  content GUID (when present) prepended or appended.

These negative results reject only those combinations. They cannot establish
keying, an algorithm, coverage, enforcement, or edited-file acceptance.
The names `SignatureMarker` and `m_privateSignature` remain the stronger
structural evidence from the source files' embedded schemas.

## Reproduction

```sh
python3 research/rvt/test_signature_analysis.py
python3 research/rvt/signature_analysis.py \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/RE1-Electrical.rvt \
  research/rvt/local/RE1-Mechanical.rvt research/rvt/local/RE1-Plumbing.rvt \
  > research/rvt/results/signature-analysis.json
```

Three boundary tests verify scalar limits, endian interpretation, and exact
field width. The report intentionally uses measured counts rather than an
unsupported probability that native export will work.
