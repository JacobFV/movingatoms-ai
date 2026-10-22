# Complete partition envelope traversal

The byte-derived `partition_segments.py` parser and serializer reproduce all
27 partition payloads in the six pinned Revit 2023–2025 fixtures exactly.
`partition-segments.json` records **523 segments and 3,736 gzip members**.
All members pass gzip CRC/ISIZE, explicit length and trailing-length checks.
No compressed-byte signature scanning is used. The parser consumes the whole
payload, including an observed optional single zero byte at its end.

The base partition header is `<u32 9, u32 0, u16 root_tag, u32 0, u32 count>`.
Each segment contains length-framed members and a kind-zero terminator,
then a counted footer blob and a counted UTF-16 label. After the footer:

- `u16 root_tag, u32 0, u32 0xffffffff` ends the partition.
- `u16 root_tag, u32 0xffffffff, u16 root_tag-1, u32 count, GUID[16]`
  introduces another segment.

All continuation GUID lists in this corpus are sorted by their stored bytes.
Their semantic role and the count fields are not inferred from sorting.
Calling them editing episodes or save transactions would be premature.

There are **521 nonempty 64-byte footer blobs**, with two empty blobs. None
matches SHA-512 of the concatenated inflated members, compressed members, or
framed member blocks. No two segments have identical concatenated inflated
bytes, so this corpus supplies no direct repeated-input test of footer
determinism. These observations do not establish cryptographic signing.

The serializer preserves the unknown footer. It does NOT regenerate its
integrity or establish validity after content changes. Exact envelope framing
is now accounted for; footer generation and semantic/index relationships
remain unresolved.

Reproduce:

```sh
python3 research/rvt/verify_segments.py research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt research/rvt/local/RE1-*.rvt
python3 -m unittest discover -s research/rvt -p 'test_partition*.py'
```
