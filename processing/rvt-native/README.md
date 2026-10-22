# Experimental native RVT transport

This crate implements the recovered Revit page parity and transactional CFB
stream replacement. It is **not a model-to-RVT exporter or semantic element
writer**. Revit acceptance has not been tested. The processing worker does not
advertise native output or call this experimental crate.

The algorithm comes exclusively from the MIT fixture bytes documented in
[the research evidence](../../research/rvt/results/README.md). Both Python and
Rust implementations reproduce 917 full pages and 69 final pages across six
licensed fixtures (986 total), including held-out Revit 2025 models. See
[complete framing evidence](../../research/rvt/results/complete-codec.md).

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
    "new_payload_file": "elem-table-payload.bin"
  }]
}
```

`new_payload_file` contains exact logical stream bytes: compressed members and
stream framing, with **all** page parity and padding removed. It is not the
inflated element buffer. The complete `codec` selects page dimensions, writes
padding lengths, and computes parity, including for resized final pages.
Nonpaged streams are replaced verbatim. All stream names must already exist.
The writer checks directory metadata (storage/stream kind, CLSID, state bits,
and timestamps) as well as every stream hash after changes.

For compatibility, `new_unpaged_file` retains the old representation: full-page
trailers removed but the final short page still encoded. Exactly one field is
required. New callers should use `new_payload_file`; stale padding metadata or
parity in legacy input is rejected by complete post-write validation.

`encode-stream INPUT OUTPUT` and `decode-stream INPUT OUTPUT` expose the complete
codec. `encode-pages`/`decode-pages` expose the legacy partial representation.
Neither corrects damaged data or authenticates files. All-zero data and final
payloads that fill a stored page despite being short are covered by tests.

The caller remains responsible for compression, object checksums, element
references, save bookkeeping, and schema/version compatibility. Passing
transport verification does not establish Revit acceptance.

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
