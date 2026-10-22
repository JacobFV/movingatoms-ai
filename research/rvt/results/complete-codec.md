# Exact payload framing (2026-10-22)

`complete-codec.json` records byte-identical decode/encode of 69 streams:
917 full pages and 69 final pages from six licensed models. The four RE1
models are held-out Revit 2025 fixtures from the MIT-licensed
[IFC-ECS repository](https://github.com/Drshelden/IFC-ECS/tree/9e8b37175a0fba1397f7011aeee917fe52de7623).
The original two fixtures cover Revit 2023/2024. Download revisions and hashes
are pinned in `fetch_fixture.py`; binaries remain ignored.

For a layout with degree m, L lanes and N codeword bits, D=(N-m)L.
The last W=max(7,m+1) coded data bits hold padding length P, in bits.
P is divisible by eight. Payload length is ceil((D-W)/8)-P/8.
The intervening bits are zero. In small layouts the last payload byte's high
zero bits can overlap the length field. Decode restores those zeros.

Choose dimensions by reserving m+1 bits, using 65 lanes with shortened
codewords or an odd number of lanes with full codewords, and minimizing
stored byte length. This predicts every observed final layout. The encoder
also considers W reserved bits to avoid discarding arbitrary nonzero payload
bits at small-layout boundaries; that extension has synthetic round-trip
coverage, but no Autodesk acceptance evidence.

A shortened payload near 64,896 bytes can occupy 65,249 stored bytes. Only the
last physical page may use nonzero padding length. Boundary tests cover this
case, all-zero data, corruption, and padded interior-page rejection.

Reproduce with:

```sh
python3 research/rvt/fetch_fixture.py
python3 research/rvt/verify_codec.py research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt research/rvt/local/RE1-*.rvt
python3 -m unittest discover -s research/rvt -p 'test_*.py'
cargo test --manifest-path processing/rvt-native/Cargo.toml
```

These results establish transport framing, not semantic validity or Autodesk
openability. Earlier episode experiments regenerated ECC but preserved stale
padding metadata; they must not be used as valid complete-framing evidence.
