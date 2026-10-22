# Evidence provenance

All results here are derived only from bytes of the two MIT-licensed models
in magnetar-io/revit-test-datasets at
`fd755e18cec40ed016d06b082f420d796571fef1`. `fetch_fixture.py` pins their hashes.
No Autodesk or ODA implementation code, binaries, or disassembly was used.

- `core2024-pages.json`: 509 full pages; all payload vectors are independent.
  Includes two Formats/Latest pages omitted by the old 507-page probe.
- `core2024-bch.json`: 336 byte-aligned cyclic-code hypotheses. Maximum common
  polynomial degree 10; none explains the parity. These layouts are wrong.
- `core2024-lanes.jsonl`: 16 byte-aligned shared affine-map hypotheses rejected.
- `hamming-discovery.json`: bit-level padding observation and polynomial GCD
  recovery from 24 codewords, without calling the encoder.
- `parity-verification.json`: the recovered encoder reproduces **all 519 full
  page trailers and all 29 eligible stored streams byte-for-byte**, across
  Core Interior and the independent Einhoven fixture. Includes short final pages.

## Recovered format

Bits are consumed least significant first within each byte. The 64,896 payload
bytes are followed by 12 zero bits, then 2,805 parity bits, then 7 zero bits.
The padded data is 2,036 words of 255 bits; parity is 11 words of 255 bits.
Each of the 255 bit lanes is a systematic binary cyclic (2047,2036) Hamming
code. The transmission-order generator is `x^11 + x^2 + 1` (`0x805`).
With the first transmitted bit as the lowest polynomial coefficient, GCD
recovers the reciprocal `x^11 + x^9 + 1` (`0xa01`).

The 353-byte trailer **is computable error-correction parity** for these
fixtures. It is not a keyed signature. This does not establish any other
integrity rules or Revit acceptance of semantic edits.

## Final-page follow-up

`partial-pages.json` corrects the original handoff: **short final pages also
carry parity**. All 29 have exactly one matching layout within the tested
family. They use 65–253 lanes, codewords up to 2047 bits, and generators
`0x13`, `0x25`, `0x43`, `0x83`, `0x211`, or `0x805` (degrees 4, 5, 6, 7, 9, 11).
The partial page can end partway through a byte. `partial_pages.py` reproduces
all matches from bytes. Selection of the layout for newly sized Revit streams
is not yet derived; exact template-based re-encoding is supported.

The Rust verifier checks **519 full pages + 29 final pages = 548**.
`rust-identity-write.json` proves an exact whole-file identity transaction.
`rust-gzip-mtime-write.json` changes only the multipage ElemTable stream,
regenerates its full-page parity, verifies its final-page parity, and checks
all other streams remain identical. `independent-reader.json` records that
rvt-rs emits byte-identical JSON for all 4,833 elements before and after.
These are structural/transport results, not Revit-openability or model export.


## Corrected History experiment

`episode-plan.json` and `rust-episode-write.json` record a properly framed
39 → 40 episode-list edit, preserving the stream prefix and all existing
episode-number-to-GUID mappings. The shortened page grows 837 → 845 bytes and
its parity is recomputed. `episode-independent-reader.json` records identical
4,833-element JSON and a byte-identical 4,467,238-byte IFC export from rvt-rs,
including 15,332 GlobalIds. This corrects the earlier invalid spike; it does
not claim a complete save transaction or Autodesk acceptance.

## Complete framing supersedes the partial-page assumptions above

See [complete-codec.md](complete-codec.md), `complete-codec.json`, and
`complete-codec-rust.json`: 986 pages across six fixtures reproduce exactly,
including their payload lengths and canonical dimensions. The earlier
`episode-plan.json` / `rust-episode-write.json` retained stale padding-length
metadata and are historical evidence only. `episode-complete.json`,
`episode-complete-writer.json`, and `episode-complete-reader.json` supersede
them. The new IFC comparison normalizes only the two export timestamps;
all other bytes match. Autodesk acceptance remains untested.
