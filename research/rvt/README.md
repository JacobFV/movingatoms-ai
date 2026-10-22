# Revit (.rvt) research scripts

See [docs/rvt-research.md](../../docs/rvt-research.md). Run with `uv run --with olefile --with xxhash --with crcmod python <script> <file.rvt>`.

- `rvtinspect.py` — list a file's OLE streams and print BasicFileInfo.
- `tail_probe.py` — split paged streams into 64,896 + 353-byte pages; entropy, constant bytes, digest search, duplicate-payload check.
- `tail_probe2.py` — more digests (xxhash, CRC variants, SHA-512, BLAKE2b) and stride-structure checks on one page's trailer.
- `hist_patch.py` — build an rvt-rs `rvt-write` patch manifest that edits the Global/History stream (the one semantic write that worked).

## Recovered parity and native transport

The trailer is solved: 255 interleaved Hamming(2047,2036) lanes, polynomial
`x^11+x^2+1`. See [recorded results](results/README.md) and the
[Rust codec/writer](../../processing/rvt-native/README.md).

```sh
python3 research/rvt/fetch_fixture.py
uv run --with olefile python research/rvt/pages.py research/rvt/local/core2024.rvt \
  --export research/rvt/local/core2024.pages
python3 research/rvt/discover_hamming.py research/rvt/local/core2024.pages
uv run --with olefile python research/rvt/verify_pages.py \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt
python3 -m unittest discover -s research/rvt -p 'test_*.py' -v
```

`paged.py` is the dependency-free reference encoder/strict verifier.
`bch_probe.py` and `lane_probe.py` document the rejected byte-aligned
hypotheses; the latter runs with `uv run --with numpy python ...`.
The original `hist_patch.py` remains historical and must not be treated as
a faithful writer: it discards original framing and creates an unrelated
invalid ElemTable manifest. Use the hash-guarded transport tool for new work.
