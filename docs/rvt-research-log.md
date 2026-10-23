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

## 2026-10-22 — Coordinated append candidate and independent identity checks

Preserved four append-save candidates as controls. The latest v4 moves the
edited room into Partitions/85, prepends History episode 703, updates its
last-modification row, and appends both increment arrays. Contents revisions,
BasicFileInfo counters, and both newest-episode GUID strings are synchronized.
The independent reader confirms all seven audited metadata relationships.
Earlier candidates demonstrate that successful element extraction alone misses
inconsistent save metadata. See [candidate report](../research/rvt/results/save-candidate.md)
and [identity audit](../research/rvt/results/save-identity.md).

The room's complete graph has 11 objects and 10 resolved pointer edges. Only
its requested floor finish changes; its creation-based UniqueId is preserved.
All 154 exported elements remain. IFC comparison exposes 860 generated-ID-only
changes following the document GUID update, plus the two expected finish and
source-stream lines. This is recorded as an unresolved projection stability
issue, not hidden by normalization. Candidate SHA-256:
`daf2424e219292b0c5661e4ad5c029717de11741e5e50f5c9c910c2801e23cae`.

Historical revision audit covers 422 increments across six files. It establishes
observed relationships, including Architecture's increment-table offset, but
does not prove a complete save policy. Global/Latest schema traversal consumes
1,663 objects across six files and four closing zero bytes per file. The selected
history/increment fields are null, zero or empty; this does not rule out deeper
references. No Revit executable or proprietary SDK was inspected.

The framing audit also checks all 24 remaining unclassified streams against the
recovered page codec. None reproduces with that framing. They remain unclassified;
this says nothing about other possible integrity checks.

```sh
python3 -m unittest discover -s research/rvt -p 'test_*.py'
```

65 tests pass. Native acceptance, nonempty unsigned partitions, ancillary revision
semantics and new element creation remain unresolved. These scripts deliberately
require acknowledgment of the experimental save hypotheses.

### Subsequent binary-header finding and screenshot checkpoint

The BasicFileInfo framing audit identified two length-prefixed UTF-16 GUID
copies and a preceding binary counter. They match the textual values in all
six source files but remain stale in v4. The candidate report now explicitly
records this additional inconsistency; v4 remains a preserved control.

Captured actual local report pages with Chrome using:

```sh
python3 research/rvt/capture_evidence.py docs/rvt-evidence/2026-10-22-save-candidate-controls
```

The new candidate panel was visually inspected. The capture reran 65 Python
tests successfully; its manifest binds screenshots, JSON reports and tested
source hashes. Corpus/Rust results in the pages are recorded evidence, not
fresh runs. The next work is a strict BasicFileInfo framing codec and a candidate
that also synchronizes binary duplicates.

## 2026-10-22 — Isolated IFC namespace cause and episode-reference scan

The public IFC exporter seeds generated identifiers from BasicFileInfo's document
GUID. An explicit persistent-namespace adapter eliminates all 860 identifier-only
changes while preserving native element/type/storey IDs. Source export is byte
identical; candidate export retains exactly the two intended property/provenance
changes. See [IFC identity audit](../research/rvt/results/ifc-identity-audit.md).
The adapter compiles against the clean pinned public reader; it does not rewrite
IFC text or alter the reader checkout. A persistent model namespace remains an
explicit caller input, with copy/fork semantics outside this experiment.

A separate raw-encoding scan of all six originals covers 109 streams and 3,784
valid gzip members. The newest History episode GUID appears only in its History
record and four BasicFileInfo UTF-16 locations under the tested encodings. This
independently confirms the two previously missed binary-header GUID copies.
[Scan evidence and limits](../research/rvt/results/save-reference-scan.md).

## 2026-10-22 — BasicFileInfo identity framing codec

Implemented a guarded codec for the observed BasicFileInfo identity records.
It updates all four counter representations and all four GUID representations,
including the binary-prefix copies missed by v4. Counter digit growth/shrinkage
is supported by rebuilding the UTF-16 record length and preserving every other
byte slice. The parser requires the observed header value, unique named text
fields, adjacent framed GUID copies, matching binary counters and a following
framed model identity GUID; unsupported layouts are rejected.

Six original streams roundtrip byte-for-byte. Twenty-four independent text-reader
trials cover counts 99, 100, 1000 and 9 with changed GUIDs; reversing each edit
restores the original bytes. Five focused tests pass. Binary semantics rely on
observed framing/cross-copy equality, because the independent BasicFileInfo reader
only decodes the text block. See [codec evidence](../research/rvt/results/basic-file-info.md).

The following model identity GUID is zero in all six originals; it supplies no
useful persistent export namespace. Unknown BasicFileInfo bytes remain preserved.

## 2026-10-22 — Fifth save candidate synchronizes binary metadata

Candidate v5 uses the structural BasicFileInfo codec. All four counter copies
and four GUID copies agree with the appended increment and newest episode;
reversing the identity edit restores the original BasicFileInfo bytes exactly.
The independent BasicFileInfo reader confirms no other text-property changes.
The new identity verifier binds every preserved control to its actual file hash
and pinned reader revision, retaining failures for earlier controls.

The current-record route, complete room graph, native identity and all 154
legacy projected elements pass the same comparisons as before. Default IFC
export still shows 860 generated-ID changes; the explicit stable-namespace
adapter removes them all, leaving the intended finish and provenance changes.
Candidate SHA-256:
`8d93244c54b86eba31482cfb4930c827f1f0716d9b516234a0c3aa3e36c1f47f`.

[Reproduction and remaining hypotheses](../research/rvt/results/save-candidate.md).
No evidence here settles unsigned nonempty partitions, ancillary revision policy,
user-modification dates or Revit acceptance.

## 2026-10-22 — Signature coverage and modification-date audits

A signature relationship audit finds four repeated ContentKeys across Mechanical
and Plumbing with mostly identical objects but different IDs, selected body
bytes, and private fields. All sequence-103 body lists match for these pairs;
the complete groups do not. ContentKey alone therefore cannot cache exact
serialized bytes or private fields. No identical complete input pair was found,
so signature determinism/keying remains undecided. The embedded-schema name
search finds no additional algorithm declaration. [Evidence](../research/rvt/results/signature-relations.md).

The independent modification-date audit covers 53,544 identities. Valid dates
satisfy creation <= user modification <= modification; 1,575 user-modification
fields instead contain 0xffffffff. Both experimental room-date variants preserve
native identity and route successfully, so reader success cannot determine
whether a user edit must advance that field. The channel-101 investigation
explicitly covers only the decoded root, not its deferred remainder.
[Evidence](../research/rvt/results/modification-history.md).

The complete Python discovery suite now passes 74 tests, including both new
audits. A historical licensed corpus search is continuing to obtain actual
same-document save transitions rather than infer temporal rules from unrelated
static files.

### Fifth-candidate screenshot checkpoint

Captured and visually inspected the fifth-candidate panel under
`docs/rvt-evidence/2026-10-22-save-v5/`. Its fresh test log records 74 passing
Python tests; its immutable manifest records source/report hashes. The panel
compares all five candidates, including binary identity, and the explicit
stable-namespace IFC adapter. This capture precedes the newly obtained
historical files and retains the six-original-file corpus scope.

## 2026-10-22 — Historical corpus exposes valid alternative page layouts

Recovered five earlier MIT-licensed Core Interior snapshots from the existing
dataset's Git history. All six Core versions share creation identity and retain
older History episodes as an exact suffix. License, commit, LFS hash/size and
retrieval provenance are recorded in [paired source evidence](../research/rvt/results/paired-save-sources.md).
These are adjacent Git snapshots, not controlled adjacent Revit saves.

Initial strict decoding rejected historical History and increment-table pages,
then Partitions/50 and Contents. Algebraic identification proved their parity
valid. The failure was our assumption that every source used the default
encoder's dimension-selection policy. Both codecs now accept a unique valid
historical layout after exact same-layout reconstruction, while retaining the
existing policy for ambiguous degenerate zero pages.

The expanded cross-language audit passes all 138 streams in eleven files:
2,760 full pages and 138 final pages. Nine historical streams differ from default
canonical re-encoding, explicitly reported rather than called byte-identical.
Every detected source layout reproduces exactly; default Python/Rust encoders
agree and roundtrip to identical logical bytes. Sixteen Rust tests and four
Python codec tests pass; Clippy is clean. [Details](../research/rvt/results/historical-codec.md).

All five chronological pairs now pass record comparisons with no unresolved
shared selections and no reused native UniqueIds. Changed bodies sometimes
retain user dates; three header changes retain both modification dates. The
reports preserve exact bytes, conservative routing and the limits of inferring
user actions from Git snapshots. [Paired changes](../research/rvt/results/paired-modification.md).

### Preserve no-op logical edits across historical layouts

The historical-layout discovery exposed another transport edge case: supplying
unchanged logical bytes through `new_payload_file` could previously re-encode a
valid historical stream into a different layout. The writer now verifies and
reuses the original stored bytes when the logical replacement is unchanged.
A synthetic noncanonical Contents transaction confirms whole-file byte identity
and an empty changed-stream list. Seventeen Rust tests pass and Clippy is clean.
Changed logical payloads still use the documented encoder policy; untouched
streams and no-op payload patches retain their original bytes.

## 2026-10-22 — Fresh DataStorage bodies and registered creation candidate

Implemented a bounded embedded-schema encoder for a new non-geometric
DataStorage element. It reconstructs the observed source bodies exactly from
named fields, then encodes a fresh name, numeric ID and storage GUID. Unknown
schema descriptors, duplicate tags/names, inherited field ambiguity, unresolved
references and inheritance cycles are rejected. File-local ES dependencies are
validated and remain explicit; this is not an arbitrary-family/geometry writer.

Fresh element 133210 has complete independently decoded channels 101/102/103,
with 119/265/2 bytes, 2/5/1 objects and 1/4/0 edges. Its outgoing element references
are self or unset. History episode 39 and a new ElemTable row preserve all
26,425 existing native identities. [Encoder evidence](../research/rvt/results/new-element.md).

A whole-file control initially omitted incoming registrations. The independent
Global/Latest audit found three required observed lists: one cell-tracking set
and two ES-schema sets. The registered candidate updates these lists. Its full
252-object/251-edge Global/Latest graph differs only by those three ID insertions
(+24 bytes); source/candidate graph evidence is bound by inflated stream hash.

Registered candidate SHA-256:
`99dcd64c7d5a881e4cdbc8bf202b05f9abaf85e06917967c0cb5ddab19de5936`.
It preserves every original partition, passes all seven metadata relationships
and all known BasicFileInfo binary/text copies, and independently routes the new
ID through all three channels. The unregistered control is retained separately.
The default exporter changes 13,830 generated IDs; a persistent namespace yields
byte-identical IFC, expected for a non-geometric DataStorage addition.
[Reproduction and limits](../research/rvt/results/create-candidate.md).

Nine focused encoder/registration tests and two creation-generator guard tests
pass. Native acceptance, all possible incoming registrations, unsigned partitions
and complete save-policy semantics remain unresolved. The next revision-policy
audit has already found unchanged stream bytes with advanced revision counters;
these candidates preserve the earlier policy as an explicit research control.

## 2026-10-22 — Retained signatures across real save history

The historical signature audit compares 307 content-group occurrences. All 729
pairs with equal complete inflated content retain the same private field (723
nonempty, six empty). Repeated nonempty private fields also retain identical
gzip/member framing. Eight complete partition payloads recur, including one
unchanged across all six Core snapshots. This supports preserving earlier groups
and their opaque integrity bytes during append experiments; it does not prove
signatures were regenerated deterministically or identify their algorithm.
[Evidence](../research/rvt/results/signature-history.md). Two comparison tests pass.

### Native creation and historical framing screenshots

Captured actual Chrome screenshots under
`docs/rvt-evidence/2026-10-22-native-creation/`. The new element-creation and
historical-layout panels were visually inspected. The capture's fresh Python
suite passes 92 tests. Its manifest binds the tested code, copied evidence and
all artifact hashes; the code snapshot follows commit `e998483` with recorded
working-tree additions. Rust/corpus counts in pages are recorded runs, not
rerun by the screenshot command.

### Evidence capture consistency

The capture generator now reads each JSON source once and uses those same bytes
for its hash, rendering inputs and archived copy, preventing a concurrent source
update from mixing versions inside one capture. All existing archived source
copies were checked against their recorded source hashes; every check passes.

## 2026-10-22 — Ancillary revision and ProjectInformation corrections

Real historical pairs disprove the old unchanged-bytes/unchanged-revision
assumption: ContentDocuments and PartitionTable remain byte-identical across
all five transitions while revisions advance; TransmissionData does so in one
pair. An explicit follow-up policy now advances contentDocuments,
transmissionData and projectXMLInfo while preserving established revision
offsets. The prior room/creation candidates remain immutable controls.

ProjectInformation's only XML changes across the five historical pairs are two
`updated` texts. Their relation to the latest increment timestamp has a measured
source offset: 14,400 seconds for Core/Einhoven, 36,000 for the four RE1 files.
The guarded ZIP patcher updates only those two texts, CRC/sizes/directory offset,
preserving all other XML bytes and ZIP metadata. It preserves the observed
source offset as a hypothesis, not a universal timezone/daylight-saving rule.
Eleven-file audit and three codec tests pass.
[Audit](../research/rvt/results/project-information.md).

Room v6 and `create-candidate-ancillary.rvt` independently pass their prior
native identity/graph/registration checks plus the new metadata checks. Relative
to their respective preceding controls, exactly three streams change:
ProjectInformation, Contents and DocumentIncrementTable. All other streams are
byte-identical, including native records and BasicFileInfo. Preview regeneration
and signature acceptance remain open. [Candidate evidence](../research/rvt/results/ancillary-candidates.md).

A separate 11-file actor audit finds no equality rule tying increment m_userName
to BasicFileInfo Username or Author: Username is empty throughout and Author is
a distinct constant. No XML author leaf was observed. Reports redact identities
and paths; two tests cover relationships and redaction.
[Actor evidence](../research/rvt/results/save-actors.md).

## 2026-10-22 — Incoming references and source preview audit

Audited all 79,275 current Core project record channels using exact or explicit
compaction routes. Thirteen signed64 byte-prefilter matches were fully decoded,
including two 16 MB geometry bodies requiring a larger bounded value budget.
No candidate graph remained unresolved. Eight external typed references to the
source wall occur in room, plan-topology and view-override records; none to the
source DataStorage occur in this audited record domain. Numeric coincidences
inside geometry are recorded separately. Existing wall references belong to the
retained wall, so they must not be blindly copied to a new translated wall.
[Reference evidence](../research/rvt/results/incoming-references.md).

The eleven-file preview audit verifies embedded PNG CRCs, framing and dimensions.
Every historical pair changes actual RGBA pixels; it is not only header metadata.
No tested save GUID or timestamp wrapper relationship was established. The
40-byte suffix contains raster dimensions/DPI, and raw source PNGs were extracted
without modification. Two preview tests and two reference traversal tests pass.

Captured and visually inspected `2026-10-22-source-previews/source-previews.png`,
a local browser contact sheet. The manifest binds exact source thumbnails and
hashes. These are original licensed source previews, explicitly not renders of
our edited candidates. Source MIT notices accompany the extracted images through
the linked license files. Every capture artifact hash was verified.


## Schema-encoded native wall and independent geometry evidence

Added a bounded straight-wall encoder that reconstructs all three source bodies exactly
from named embedded-schema fields (106 objects, 103 edges), then assigns a fresh identity
and translates the measured world-coordinate fields. The writer preserves all 26,425
existing identities and original partitions, registers the new wall in Global tracking,
and applies the observed save bookkeeping. The outside variant moves 400 feet along X
and disables the two measured bounding booleans with explicit hypothesis acknowledgment.

IfcOpenShell 0.8.5/OpenCASCADE independently verifies every one of the 360 previous wall
meshes and the new 8-vertex/12-triangle wall. Its dimensions are 2.8956 × 0.2032 × 4.572 m,
volume 2.69010042624 m³, displacement 121.92 m, and material matches the source. Separate
IFC OwnerHistory correction controls resolve a pre-existing exporter schema violation;
all other STEP attributes remain unchanged. These controls do not modify RVT files.

Recorded actual mesh arrays, report hashes, plot measurements and a headless Chrome
screenshot in [wall geometry evidence](rvt-evidence/2026-10-22-wall-geometry/manifest.json).
Visually inspected the screenshot. Full Python discovery passed 114 tests, including
the two initial parametric integration guard tests; this checkpoint does not claim the
pending length-change experiment is complete. Native regeneration, foreign-producer
encoding and acceptance remain unverified.

The [public-source audit](../research/rvt/results/signature_public_sources.md) corrects
the old signature dead-end premise: Autodesk documents desktop opening of foreign RVT
files. It does not identify our partition field or establish cloud acceptance.


## Parametric wall length and independent IFC mesh

Extended the measured wall from 9.5 to 12 feet while retaining its start, thickness,
height, type and level context. The encoder transforms named world-coordinate fields
and face-local UV distances together, preserving unit directions and topology. The
candidate SHA is `271c54903276ebc540206979d8b54d008aec485fb823704433633f909de54c39`.
Only its new Partitions/66 stream differs from the verified translated-wall control.

The pinned native reader consumes all three new graphs completely; original wall
objects and existing projected elements/identities remain unchanged. Independent
IfcOpenShell/OpenCASCADE triangulation measures a 3.6576 × 0.2032 × 4.572 m wall and
3.39802159104147 m³ volume, preserving all 360 prior wall meshes exactly. Explicit
OwnerHistory correction controls pass schema validation with zero messages.

[Actual mesh screenshots and hashes](rvt-evidence/2026-10-22-parametric-wall/manifest.json)
are archived and visually inspected. The copied reports are immutable snapshots from
before the subsequent machine-readable validation-boundary annotation. All capture
artifact hashes verified. This IFC result does not alone validate the saved native
BRep; a separate native face/edge/solid audit follows.


## Saved native BRep and foreign-producer search

A separate verifier reconstructs face loops and edge endpoints from the actual saved
candidate's independently decoded channel 103 graph. It does not use SWall driver
parameters or IFC. It verifies opposite directed edge incidence, a closed six-face,
twelve-edge, eight-vertex solid, Euler characteristic two, 120.00000000000085 ft³
volume and 396.0000000000002 ft² surface area. Four auxiliary open sheets are reported
separately. Native vertices match the saved bounds; the final audit also checks the
header Outline. Negative tests reject broken topology, UV geometry and bounds.
The [native BRep screenshot](rvt-evidence/2026-10-22-native-brep/wall-comparison.png)
was captured before the final header-Outline check was added; its immutable source
report accurately records the earlier checks. Screenshot visually inspected and hashes verified.

A [bounded foreign-producer search](../research/rvt/results/foreign_producer_search.md)
found no downloadable model with both permissive licensing and established third-party
writer provenance. Safe Software's official FME tutorial corroborates opening a foreign
RVT through Revit's warning. No foreign bytes or proprietary implementation were inspected.
This leaves the valid producer-field encoding and native acceptance unresolved.

Final integrated Python discovery passes **128 tests**. No Rust transport code changed in this checkpoint.


## Multi-wall transaction and one-command validation (2026-10-23 UTC)

Extended the bounded writer to accept multiple length/XY specifications. It validates
all new bounds, rejects duplicate/touching/intersecting walls, allocates sequential IDs
in one episode, and writes all records into one partition. An independent bookkeeping
audit caught and eliminated the former single-object increment count: both count fields
now reflect the batch size in both increment arrays. Global registration is one guarded
sorted union rather than repeated application of stale source offsets.

Added `wall_batch_experiment.py`: writer, independent metadata auditor, pinned native
reader/BRep checks and IfcOpenShell checks run before no-clobber publication. Every report
must bind the same candidate SHA, and research code/source/writer hashes must remain
stable. Failed runs preserve logs and staging evidence with an explicit failed status.

The complete three-wall run passed: native solid volumes 60/120/180 ft³, all 26,425 prior
native identities, eight original partitions and 970 projected entities retained. All
360 original IFC wall meshes remain exact; 363 total walls. Explicit IFC OwnerHistory
controls pass schema validation with zero messages. Candidate SHA:
`3f34208b1d94bb99663601aefe1a2054cd3c7e39d695f4abf193401f24967bf6`.

The full Python suite passes **143 tests**. No Rust transport code changed. Actual mesh
plots and report snapshots were captured in Chrome, visually inspected, and all artifact
hashes verified: [batch evidence](rvt-evidence/2026-10-23-wall-batch-corrected/manifest.json).
Native regeneration/foreign producer framing/Autodesk acceptance remain unverified.

Visual QA rejected the first batch plot: Matplotlib modified a reused aspect array,
clipping panels two and three. Passing a copy fixes the renderer. The rejected capture
is retained with `REJECTED.md`; the corrected screenshot is the documentation default.
No candidate bytes, mesh data or validation results changed. Corrected capture hashes
were verified and its three panels visually inspected.


## 100-wall boundary and compression stress

Executed the same complete workflow at its 100-wall request limit using 6/12/18-foot
lengths and alternating Y placements. All four stages passed. New IDs 133210–133309
share one episode; both increment counts are 100. The new logical partition is 33,939
bytes with ten gzip members, exercising cross-member object reconstruction. Independent
saved-solid volumes total 11,940 ft³; IFC has 460 walls, with all 360 original meshes exact.
Both explicit corrected IFC controls have zero schema messages. Original identities,
rows, source partitions and projected entities remain preserved.

Candidate SHA: `5e33e3a6489fa6d5d5430de51addcea30023cd5ca6a36f302d65d844e961711a`.
The run records clean committed code from 17d18b2 and source/tool/report hashes. Archived
full metadata/native/IFC/mesh results plus a representative three-mesh screenshot with
explicit 100-wall labeling. Screenshot visually inspected and artifact hashes verified.
The three-wall capture is preserved separately. This adds size/boundary coverage; it
does not resolve native regeneration or Autodesk acceptance.


## Rotated-wall integration: verifier representation mismatch

The first 45°/90°/−30° run passed metadata and saved native BRep checks but failed
the public projection comparison before publishing a verified artifact. The failed
run, metadata and exact stderr are retained in `results/wall-oriented-failed-*`.
Investigation found the 90° wall uses an equivalent IFC representation: local width
and depth swap and the placement frame is unrotated. The resulting physical corners
are equivalent; requiring the original parameterization was a verifier error.
The correction will compare complete physical geometry and material direction.

The pinned public STEP writer also emits placement coordinates and directions with
six decimal places. Independent IFC validation must account for that explicit
serialization precision while retaining strict saved-native-coordinate checks.


## Rotated-wall workflow passes

The corrected full workflow passes on the same native candidate bytes as the failed
run: `9a8f89c26c6e530d802ddd918612a18948b366446b6a0940478a6c3464086556`.
The 45°/90°/−30° native solids match independently transformed vertices, surface areas,
volumes and saved bounds. All original identities/partitions/projected entities and
360 original wall meshes are retained. Corrected IFC controls have zero schema messages.

The verifier validates physical equivalence before deriving the exact six-decimal
serialized placement. Actual IFC vertices match that strict oracle within 1e-8 m;
ideal native vertices retain their 1e-7 ft tolerance. Maximum measured ideal-to-IFC
vertex drift is about 0.624 micrometres, explicitly attributed to serialization.
Material thickness axis, direction and offset are checked for swapped local frames.

All **154 Python tests** pass, including wrong-angle/origin/frame negative cases and
zero-yaw byte equivalence. The screenshots and full native/IFC reports are archived;
visual inspection and artifact-hash verification passed. The original failed run is
retained, including proof that no verified artifact was published on failure.
No production native-output claim or Autodesk acceptance claim is made.


## Production export contract: correct physical level units

The native-format work exposed an existing IFC unit mismatch. The production
IfcOpenShell API defaults to millimetres, while level elevations were written
directly from metre-valued model coordinates. A 3.5 m level therefore appeared
as 0.0035 m, even though the mesh API converted the geometry correctly.
The exporter now explicitly assigns SI metre, square-metre and cubic-metre units.

Regression tests independently triangulate exported geometry and compare physical
storey elevations and wall dimensions at both +3.5 m and −2.25 m. The model and
model-job suites pass: **16 tests**. This fixes the existing IFC deliverable; it
does not change the experimental native-output capability claim.


## Minimal project seed and document lifecycle audit

A pinned MIT-licensed Revit 2024 Project.rvt from ricaun.Revit.FileInfo is a
434,176-byte project with 2,300 scaffold elements and no decoded donor-building
instances. The independent reader decodes all 6,900 current channel records
completely with zero off-route records. Storage codecs and transport parity pass.
Fixture/license provenance, a reproducible fetcher, inventory and two passing
provenance tests are recorded in `research/rvt/results/minimal_seed.md`.
This provides a smaller seed; schema/context remapping remains implementation work.

A real Chrome screenshot of the archived inventory is stored in
`docs/rvt-evidence/2026-10-23-minimal-seed/`. It was visually reviewed; all manifest
artifact hashes match. It is explicitly a local evidence report, not Revit UI.

The separate `document-lifecycle.md` audit compares complete Global graphs of
the Core source and 100-wall candidate. The only semantic change is the known
structural-element set (+100 IDs, +800 bytes). No additional global bound or
registration field is demonstrated by that audit. Its historical incoming-scan
limits are identified explicitly; no claim of native cache regeneration follows.
