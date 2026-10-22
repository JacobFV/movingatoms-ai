# Experimental native RVT transport

This crate implements the recovered Revit page parity and transactional CFB
stream replacement. It is **not a model-to-RVT exporter or semantic element
writer**. Revit acceptance has not been tested. The processing worker does not
advertise native output or call this experimental crate.

The algorithm comes exclusively from the MIT fixture bytes documented in
[the research evidence](../../research/rvt/results/README.md). Both Python and
Rust implementations reproduce 519 full-page trailers and 29 shortened final
pages in two fixtures (548 total).

```sh
cargo test --manifest-path processing/rvt-native/Cargo.toml
cargo clippy --manifest-path processing/rvt-native/Cargo.toml --all-targets -- -D warnings
cargo build --release --manifest-path processing/rvt-native/Cargo.toml
processing/rvt-native/target/release/ma-rvt-native verify research/rvt/local/core2024.rvt
```

## Stream replacement

`patch INPUT OUTPUT MANIFEST` copies the original CFB container, verifies its
SHA-256 and every existing paged stream, applies all requested replacements,
recomputes full-page parity, verifies full/final-page parity and every stream's expected hash, then publishes the
new file atomically. It refuses existing output paths. Failed transactions
leave the input unchanged and publish no output. An identity transaction is
whole-file byte identical. Existing stream entries are preserved rather than
rebuilding CFB storages and losing unknown metadata.

The manifest is strict JSON; byte-file paths resolve relative to the manifest:

```json
{
  "input_sha256": "SHA256_OF_ORIGINAL_RVT",
  "patches": [{
    "stream": "Global/ElemTable",
    "expected_stored_sha256": "SHA256_OF_ORIGINAL_STORED_STREAM",
    "new_unpaged_file": "elem-table-logical.bin"
  }]
}
```

`new_unpaged_file` contains the **compressed stream bytes with full-page
trailers removed**, including its existing prefix, gzip headers/footers,
member boundaries, and opaque suffix bytes. It is not the inflated element
buffer. Nonpaged streams are replaced verbatim. All names must already exist.
The caller is responsible for compression, object checksums, reference/index
updates, schema/version compatibility, and any unresolved stream framing.

The `paged` codec retains short final pages in their encoded form. The writer
validates those final pages using `final_page::decode`, which infers and checks
the shortened Hamming layout. `final_page::encode` re-encodes a padded data bit
vector against an explicit layout. A caller changing final-page data must use
that API and supply valid final-page parity in `new_unpaged_file`; stale parity
is rejected. Layout selection for newly sized streams is not yet derived.
Some gzip members have extra data/padding before final-page parity; preserve it
until its meaning is established.

`encode-pages INPUT OUTPUT` and `decode-pages INPUT OUTPUT` expose the codec
for standalone binary streams. Decoding checks parity and all padding bits;
it rejects incomplete trailers when their length is distinguishable from a
short final page. It does not correct damaged data or authenticate files.

## Reproduced real-file experiments

```sh
python3 research/rvt/fetch_fixture.py
uv run --with olefile python research/rvt/transport_experiment.py \
  research/rvt/local/core2024.rvt research/rvt/local/identity --mode identity
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/core2024.rvt research/rvt/local/core2024-identity.rvt \
  research/rvt/local/identity/manifest.json
uv run --with olefile python research/rvt/transport_experiment.py \
  research/rvt/local/core2024.rvt research/rvt/local/gzip-mtime --mode gzip-mtime
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/core2024.rvt research/rvt/local/core2024-gzip-mtime.rvt \
  research/rvt/local/gzip-mtime/manifest.json
```

Choose fresh output paths on subsequent runs. The second experiment changes
only gzip MTIME in the multipage ElemTable stream, exercising a real changed
page and regenerated trailer while preserving the inflated element table and
opaque suffix exactly. It is a transport experiment, not a semantic edit.
