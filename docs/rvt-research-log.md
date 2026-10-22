# RVT research work log

Companion to the [technical briefing](rvt-research.md) and
[screenshot/evidence archive](rvt-evidence/README.md). Times are UTC. Findings
come from licensed file bytes and public clean-room reader code. No proprietary
Revit implementation is used. Native production export is not yet complete.

## 2026-10-22 — Earlier implementation milestones, recorded retrospectively

These entries summarize existing commits and their recorded evidence. The
screenshots below were captured later and are not contemporaneous screenshots
of the original experiments.

| Commit | Work completed | Primary evidence |
| --- | --- | --- |
| `b7bfd6a` | Strict element-table codec; 53,544 rows reproduced, owner and History relationships checked | [Element tables](../research/rvt/results/element-tables.md) |
| `30b2176` | Variable-length object repacking; real room finish grew by 26 bytes | [Object writer](../research/rvt/results/object-writer.md) |
| `fb0b709` | Schema-directed save bookkeeping and explicit revision routes; exposed 17 exceptions | [Bookkeeping](../research/rvt/results/bookkeeping.md) |
| `d92645d` | Conservative physical selection using explicit compaction links or sole holders | [Selection evidence](../research/rvt/results/record-selection.json) |

The corpus repacking preserved 736,332 records in 523 groups. The independent
reader verified one changed room property and one IFC property. The complete
owning graph retained 11 serialized objects and 10 pointer edges. These
observations do not establish signature generation, complete save behavior,
new-element creation or Autodesk acceptance.

## 2026-10-22 22:37 UTC — Start durable screenshot capture

**Request:** keep codebase documentation and screenshots as work progresses so
we can report the work later; parallel investigations are authorized.

**Change:** added `research/rvt/capture_evidence.py`, this log, and the evidence
archive. The capture runs the Python regression suite, renders two local report
pages in Chrome, and records source/artifact hashes and working-tree state.

**Command:**

```sh
python3 research/rvt/capture_evidence.py docs/rvt-evidence/2026-10-22-baseline
```

**Observed:** 37 Python tests passed. Both screenshots were captured successfully.
The room-edit screenshot was visually reviewed for readable content and limits.

- [Corpus screenshot](rvt-evidence/2026-10-22-baseline/corpus.png)
- [Room-edit screenshot](rvt-evidence/2026-10-22-baseline/room-edit.png)
- [Capture manifest](rvt-evidence/2026-10-22-baseline/manifest.json)
- [Test transcript](rvt-evidence/2026-10-22-baseline/tests.txt)

**Interpretation:** screenshots show local research reports, not Revit. The
corpus/reader JSON was copied from prior verified results; this capture reran
the regression suite, not all fixture experiments. Source revision is
`d92645d`, with the capture implementation uncommitted at capture time as
recorded in the manifest.

**Parallel work started:** independent save-table serialization and signature
analysis. Results will be recorded as they finish; starting a task is not
recorded as a successful outcome.

## 2026-10-22 — Parallel save-table and signature investigations

**Save table:** implemented `save_increments.py` and an independent corpus
audit. All 844 records (422 persistent and 422 local increment records) and
125,144 inflated bytes across six files reconstruct exactly. All decoded
fields match the pinned public reader's schema traversal. Review found that
nonempty permutation arrays were not supported by the corpus evidence; the
codec now rejects them instead of assuming flat integers. Five codec tests
cover truncation, flags, Unicode, integer bounds, changed revisions and this
unsupported case. [Results and commands](../research/rvt/results/save-increments.md).

**Signature analysis:** examined 521 nonempty 64-byte fields. Of these, 480
fail the scalar bound required by standard canonical raw Ed25519 in `R || S`
layout. No match occurred in 56,268 explicitly enumerated digest/coverage
comparisons. This does not prove a secret key or identify the algorithm. Both
unsigned source groups contain zero elements, so they are not evidence that
unsigned nonempty output is accepted. Three boundary tests check the shape
probe. [Results and commands](../research/rvt/results/signature-analysis.md).

**Verification:** reviewed both changes; reran the save audit and compared its
JSON byte-for-byte with the recorded result. All 45 Python regression tests
passed after integration. Raw source fixtures remain outside Git.

**Limitations:** save revision advancement and full transaction semantics are
not established. Signature generation, native element creation and Autodesk
acceptance remain open. Screenshots are presentation evidence for these
measured results, not substitutes for those missing checks.


## 2026-10-22 22:40 UTC — Capture save/signature milestone

Implementation and results committed as `320baea`; initial capture tooling and
archive committed as `a746a22`. Captured the updated reports with:

```sh
python3 research/rvt/capture_evidence.py docs/rvt-evidence/2026-10-22-save-signature
```

The fresh regression run passed all 45 tests. The investigation screenshot was
visually reviewed; artifact SHA-256 checks passed for both capture directories.

- [Investigation screenshot](rvt-evidence/2026-10-22-save-signature/investigations.png)
- [Room edit and current test run](rvt-evidence/2026-10-22-save-signature/room-edit.png)
- [Manifest](rvt-evidence/2026-10-22-save-signature/manifest.json)

Next implementation started: complete History decoding/encoding with corpus
checks. This is recorded as work in progress, not a completed save feature.

## 2026-10-22 — History codec and new-partition transport

**Parallel changes:** complete observed History codec and guarded episode
prepend; atomic creation of absent numeric partition streams in the Rust
transport writer. [History evidence](../research/rvt/results/save-history.md)
and [transport evidence](../research/rvt/results/transport-create.md) contain
commands, hashes, contracts and limitations.

**History observations:** 21,521 bytes and 1,181 episodes across six files
reproduce exactly. Independent schema decoding confirms every root field and
episode GUID/strength before and after a test prepend. Review corrected the
signed i32 interpretation of sequence/deficit fields using embedded descriptors.
The tests include signed boundaries and reject unsupported allocation states.

**Transport observations:** 14 Rust tests pass, Clippy reports no warnings.
A licensed RE1 Architecture control adds a copy of `Partitions/80` under the
absent name `Partitions/999999`; all 15 original streams remain unchanged.
This operation validates CFB/page transport only. It deliberately does not
claim to add a model element or link a complete save transaction.

**Reporting improvement:** capture manifests now hash the tested Python and
Rust source files and reject code changes during the test run. Earlier capture
manifests retain their original format and are not rewritten.


## 2026-10-22 22:44 UTC — Capture History/transport milestone

Implementation committed as `cbdc8e0`. Captured and visually reviewed the
[History/transport report](rvt-evidence/2026-10-22-history-transport/save-pipeline.png).
The capture reran all 50 Python tests successfully; its 14-test Rust result
comes from the recorded transport verification, not a second Cargo run.
[Manifest](rvt-evidence/2026-10-22-history-transport/manifest.json) includes exact
source hashes and verifies that sources stayed unchanged during the test run.
All artifact hashes were checked after capture.

```sh
python3 research/rvt/capture_evidence.py docs/rvt-evidence/2026-10-22-history-transport
```

## 2026-10-22 — Resume coordinated save-candidate work

Started parallel revision-rule auditing and a guarded, pinned append-save
candidate. These are active investigations, not a complete-save claim.

Implemented `partition_builder.py`: constructs a complete single-base-group
partition from the three ordered record sequences, derives counts and
sentinels, packs whole/split members and verifies the encoded envelope. It
rejects mismatched profiles, duplicate/sentinel input IDs and inconsistent
sequence lists. Nonempty unsigned output requires an explicit experimental
opt-in because source evidence does not establish acceptance. It does not
encode class bodies or generate signatures.

Three focused tests passed:

```sh
python3 -m unittest discover -s research/rvt -p 'test_partition_builder.py'
```

The tests cover empty groups in all observed profiles, split large records,
input preservation and failed preconditions. Save integration and revision
rules will be recorded separately when their checks finish.

## 2026-10-22 — Correct omitted Contents framing and save linkage

Independent identity research found that the `Contents` stream carries the
latest stream revisions and uses the recovered page ECC. Earlier stream
classification omitted it. Added `Contents` to the Rust writer's paged-stream
classification and the Python complete-codec audits. The Rust writer now
encodes logical Contents payloads and rejects corrupt Contents parity.

A new transaction regression test passed; the Rust suite now has 15 passing
tests and Clippy is clean. `verify_contents_codec.py` verifies all six original
Contents streams byte-for-byte using both Python and Rust and reruns each
file's complete Rust inventory. See
[Contents codec evidence](../research/rvt/results/contents-codec.json).
The audit initially reused a temporary output filename, which the CLI correctly
refused to overwrite; it now uses a separate directory per fixture.

```sh
python3 research/rvt/verify_contents_codec.py \
  processing/rvt-native/target/release/ma-rvt-native \
  research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt \
  research/rvt/local/RE1-*.rvt
cargo test --manifest-path processing/rvt-native/Cargo.toml
cargo clippy --manifest-path processing/rvt-native/Cargo.toml --all-targets -- -D warnings
```

The first append candidate's current-room routing passed while its Contents
revision index was stale. A corrected second candidate fixes this index;
BasicFileInfo's increment count/version remains another independently observed
mismatch to address. Earlier candidates are preserved as controls, not erased
or described as complete saves.
