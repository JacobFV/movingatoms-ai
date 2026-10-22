# Atomic partition stream creation

On 2026-10-22 the Rust transport gained an explicit `creates` manifest operation.
It accepts exact nonempty logical bytes for a new canonical `Partitions/<u64>`
stream under an existing storage. `expected_absent: true` is required. It can
be combined atomically with existing stream replacements. All original streams
and directory metadata remain checked, and output publication refuses overwrite.

Validation: six codec unit tests and eight transactional tests pass; Clippy
with `--all-targets -- -D warnings` is clean. New tests cover short/multiple-page
creation combined with replacement, eleven failure cases, optional operation
compatibility, and output refusal. Failures leave both input and output state
unchanged. The new report field `created_streams` distinguishes new entries
from changed existing streams.

A licensed RE1-Architecture control copied the complete logical payload of
`Partitions/80` into `Partitions/999999` without changing any original stream.
The writer verified 16 streams, 187 full pages and 11 final pages. An independent
Python olefile comparison confirmed all 15 original stored streams unchanged,
only one new stream, and byte-identical stored content between the new stream
and source partition. Exact hashes and commands are in
[transport-create.json](transport-create.json).

**This is not an append save or a valid model edit.** No History/Latest link,
element-table update, element creation or signature generation was attempted.
It establishes the lower-level operation required for a future coordinated
save implementation. Native acceptance remains untested.

## Reproduce the real-file transport control

Use a fresh output path on repeated runs. Creation timestamps can change the
whole-file output hash; exact stored-stream identity remains the comparison.

```sh
cargo test --manifest-path processing/rvt-native/Cargo.toml
cargo clippy --manifest-path processing/rvt-native/Cargo.toml --all-targets -- -D warnings
python3 - <<'PY'
import sys, json, hashlib
from pathlib import Path
sys.path.insert(0, 'research/rvt')
import olefile
from codec import decode
folder = Path('research/rvt/local/transport-create')
folder.mkdir(exist_ok=True)
source = Path('research/rvt/local/RE1-Architecture.rvt')
with olefile.OleFileIO(source) as f:
    payload = decode(f.openstream('Partitions/80').read())
(folder / 'partition.bin').write_bytes(payload)
(folder / 'manifest.json').write_text(json.dumps({
    'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'patches': [],
    'creates': [{'stream': 'Partitions/999999', 'expected_absent': True,
                 'new_payload_file': 'partition.bin'}]}, indent=2) + '\n')
PY
processing/rvt-native/target/debug/ma-rvt-native patch \
  research/rvt/local/RE1-Architecture.rvt \
  research/rvt/local/transport-create/control.rvt \
  research/rvt/local/transport-create/manifest.json
```
