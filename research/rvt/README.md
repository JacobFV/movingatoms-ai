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

`codec.py` is the complete reference encoder/strict verifier. `paged.py`
retains the historical partial-page representation for compatibility.
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
prefix, selects dimensions for the resized payload, and regenerates its padding
length and parity. The complete framing rule is tested against six fixtures;
see [complete codec evidence](results/complete-codec.md).

rvt-rs 0.6.1 (`b6086d41b9758fd9b92f42f0a47b8345b9c58056`) re-reads the
result into byte-identical element JSON and a byte-identical IFC export,
including all 15,332 IFC GlobalIds. **This is not a full save transaction**:
other bookkeeping is unchanged and Revit acceptance is still untested.

## Reproducible external-validation bundle

Build the Rust CLI and obtain the documented pinned rvt-rs reader binaries.
Then use a fresh destination:

```sh
python3 research/rvt/validation_bundle.py research/rvt/local/core2024.rvt \
  research/rvt/local/validation-new \
  --writer processing/rvt-native/target/release/ma-rvt-native \
  --elements research/rvt/local/rvt-elements --ifc research/rvt/local/rvt-ifc
```

The bundle contains identity, gzip-MTIME, and History candidates, IFC exports,
strict manifests, file/tool hashes, and `VALIDATE.txt`. It checks all element
JSON bytes and all IFC bytes except exactly two exporter timestamps. The
recorded run is [validation-bundle.json](results/validation-bundle.json).
No uploads occur and Autodesk results remain `not_tested` until independently
observed. Viewer conversion success alone does not prove editable Revit saves.

`partition_audit.py` separately verifies explicitly framed gzip members up to
the first segment terminator and records the unresolved footer. See
[partition-audit.md](results/partition-audit.md) before attempting model writes.

`partition_segments.py` extends the first-segment audit to a strict complete
partition envelope parser/serializer. [Recorded evidence](results/partition-segments.md)
covers all 523 segments and 3,736 gzip members, with byte-identical
reconstruction. Unknown footer bytes are preserved, not regenerated.

`parameter_experiment.py` produces a pinned, same-length room floor-finish
edit plus recompression/footer controls. `data_objects.py` verifies the owning
object's length and Adler-32 before editing and recomputes its checksum.
[Room-edit evidence](results/room-finish.md) demonstrates exactly one changed
reader/IFC property. It does not establish Autodesk acceptance or regenerate
the unresolved footer. The footer-control artifact is deliberately corrupted
at that field for future differential validation, not a production output.

`partition_objects.py` decodes and encodes object envelopes, validates split
objects and Adler-32, and checks the three matching ID lists and terminal
sentinels. [Object evidence](results/partition-objects.md) covers 736,332 records
in the licensed corpus. Class bodies and signature generation remain outside
this envelope encoder.

`schema_probe.py` / `schema_probe.rs` bind observed partition tags to names in
the files' embedded schemas, using a clean pinned public rvt-rs checkout.
[Schema evidence](results/schema-bindings.md) identifies `SignatureMarker` and
its private/public signature fields. The algorithm and Autodesk enforcement
remain unverified. `unsigned-control` and `unsigned-room-finish` experiment
modes clear both fields using the empty representation observed in source
files; their acceptance for nonempty data is not assumed.

`signature_bundle.py LOCAL_DIRECTORY OUTPUT.zip` packages the five prebuilt
signature/parameter experiments and licensed original, after checking file
hashes and exact expected reader projections. Its `VALIDATE.txt` distinguishes
Autodesk open, Viewer conversion, and Revit save/reopen checks. No upload is
performed. The recorded package is `local/signature-validation.zip`, with
[manifest evidence](results/signature-validation.json).

`element_table.py` preserves the project table's opaque fields while validating
IDs, owner references and acyclic owner chains. `verify_element_tables.py`
checks exact re-encoding and joins the table to History and partition object
lists. [Table evidence](results/element-tables.md) distinguishes project IDs
from GUID-keyed content IDs; it does not implement new-element allocation.
