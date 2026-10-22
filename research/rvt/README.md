# Revit (.rvt) research scripts

See [docs/rvt-research.md](../../docs/rvt-research.md). Run with `uv run --with olefile --with xxhash --with crcmod python <script> <file.rvt>`.

- `rvtinspect.py` — list a file's OLE streams and print BasicFileInfo.
- `tail_probe.py` — split paged streams into 64,896 + 353-byte pages; entropy, constant bytes, digest search, duplicate-payload check.
- `tail_probe2.py` — more digests (xxhash, CRC variants, SHA-512, BLAKE2b) and stride-structure checks on one page's trailer.
- `hist_patch.py` — historical spike script; not a valid writer for the pinned fixture.

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


## Corrected episode-list experiment

```sh
uv run --with olefile python research/rvt/episode_experiment.py \
  research/rvt/local/core2024.rvt research/rvt/local/episode \
  --guid e57363ed-8a74-4f26-a038-cfe940d89d70
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/core2024.rvt research/rvt/local/core2024-episode.rvt \
  research/rvt/local/episode/manifest.json
```

This experiment accepts only the hash-pinned MIT fixture. It changes both
History counts from 39 to 40 and prepends a correctly terminated episode,
preserving the episode numbers of all previous GUIDs. It preserves the gzip
prefix and unused data suffix, constructs a slightly longer shortened page,
and regenerates its parity. The current experiment keeps the same generator
and lane count; no general Revit layout-selection rule is claimed.

rvt-rs 0.6.1 (`b6086d41b9758fd9b92f42f0a47b8345b9c58056`) re-reads the
result into byte-identical element JSON and a byte-identical IFC export,
including all 15,332 IFC GlobalIds. **This is not a full save transaction**:
other bookkeeping is unchanged and Revit acceptance is still untested.
