# Newest episode GUID occurrence scan

Across six licensed originals, the newest History episode GUID occurs in four
UTF-16 little-endian BasicFileInfo locations and once in its raw little-endian
History record. No other exact occurrence was found in the tested encodings.
This independently locates the two binary-header and two text-property copies
that the coordinated save must consider.

The scanner covers 109 streams after removing known page framing and 3,784 valid
gzip members. It tests raw UUID byte orders, canonical lowercase UTF-8 text and
UTF-16 little-endian text. Reports retain file hashes, stream names and offsets;
they do not dump model properties or private paths. Gzip offsets are relative
to logical stream bytes, while match offsets inside gzip are inflated offsets.

This is an exact-byte search, not a semantic reference decoder. It does not
exclude uppercase text, other encodings/compression, derived hashes or indirect
references. It does not decide save behavior or establish Revit acceptance.

```sh
python3 research/rvt/save_reference_scan.py \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/RE1-Electrical.rvt \
  research/rvt/local/RE1-Mechanical.rvt research/rvt/local/RE1-Plumbing.rvt \
  > research/rvt/results/save-reference-scan.json
```
