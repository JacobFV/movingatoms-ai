# Historical page-layout extension

The eleven licensed files (six originals and five earlier Core snapshots) pass
strict Python/Rust transport decoding across 138 paged streams: 2,760 full pages
and 138 final pages. Both implementations agree on every logical byte. Every
source final layout is unique in this corpus and reproduces exactly with its
identified dimensions and generator. Full-page parity is also checked.

Nine historical streams do not reproduce with the default encoder selection
policy: all five historical Contents streams, Partitions/50 in two snapshots,
History in `8946a8ca`, and DocumentIncrementTable in `ede6e635`. The previous
assumption that the smallest selected encoding represented every source was
too strong. The source layouts are valid; no checksum bypass was needed.

| Historical final payload | Lanes | Codeword bits | Generator |
| --- | ---: | ---: | --- |
| Contents, 308 bytes | 65 | 44 | 0x43 |
| Partition, 4,136 bytes | 67 | 511 | 0x211 |
| History, 739 bytes | 65 | 98 | 0x83 |
| Increment table, 1,697 bytes | 65 | 218 | 0x211 |

Decoding now accepts these unique alternatives only after verifying parity,
footer length, zero padding, supported dimensions, and exact reconstruction
using the same layout. Degenerate zero pages retain the existing encoder-policy
precedence because parity alone can admit several interpretations. No universal
Revit layout-selection algorithm is claimed. The explicit-layout encoders are
available for source-preserving reconstruction; the default encoders keep their
previous selection policy.

For all streams, Python/Rust default encoders agree and the Rust decoder reads
their output back into the original logical bytes. This payload roundtrip does
not prove Autodesk accepts an alternative layout. Unchanged streams in writer
transactions remain byte-preserved; newly encoded streams use the documented
encoder policy.

Sixteen Rust tests pass, including historical-layout regressions and corrupt
page rejection; Clippy is clean. Four Python codec tests pass. Actual file,
stream and writer hashes plus all observed layouts are recorded in the JSON.

```sh
python3 research/rvt/historical_codec_audit.py \
  processing/rvt-native/target/release/ma-rvt-native \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/RE1-Electrical.rvt \
  research/rvt/local/RE1-Mechanical.rvt research/rvt/local/RE1-Plumbing.rvt \
  research/rvt/local/core-history-*.rvt > research/rvt/results/historical-codec.json
```
