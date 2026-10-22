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
