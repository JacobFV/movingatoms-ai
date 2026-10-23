# Writing native Revit (.rvt) without Revit — research notes

Latest implementation: a [single-command multi-wall workflow](../research/rvt/results/wall-batch.md)
creates multiple distinct walls in one partition/episode, with independently verified
native solids and IFC meshes. Three-wall, 100-wall and [rotated-wall](../research/rvt/results/wall-oriented.md) runs passed. All 26,425 original identities and 360 original wall
meshes are preserved; 154 Python tests pass. This remains a pinned-source research
writer with unverified native regeneration, producer encoding and Autodesk acceptance.

A [minimal MIT-licensed 2024 project seed](../research/rvt/results/minimal_seed.md)
has now been identified: 434 KB, 2,300 scaffold elements, all 6,900 current records
fully decoded and no decoded donor-building instances. Seed-specific schema,
reference and save integration are in progress.

Current save experiment: [candidate v6](../research/rvt/results/save-candidate.md)
passes independent room routing/full-graph checks, seven Contents/text metadata
relationships, and all observed binary BasicFileInfo identity copies. An explicit
persistent-namespace IFC adapter removes generated-ID churn. This remains an
unsigned experimental edit. A separate [registered DataStorage creation candidate](../research/rvt/results/create-candidate.md)
adds one bounded non-geometric element and preserves all existing identities.
[Ancillary variants](../research/rvt/results/ancillary-candidates.md) additionally synchronize
observed revision counters and ProjectInformation timestamp copies.
Full save semantics, arbitrary geometry creation and native acceptance remain unresolved. [Screenshots and evidence](rvt-evidence/README.md).

A [schema-encoded straight-wall candidate](../research/rvt/results/wall-candidate.md)
now adds a fresh native wall with fully reconstructed geometry and measured Global registration.
Independent IfcOpenShell/OpenCASCADE checks preserve all 360 existing wall meshes and verify
the new wall's dimensions, volume, material and translation. The outside-model variant
sets two measured room/space-bounding booleans false; native regeneration remains a hypothesis.
[Actual mesh evidence and screenshot](rvt-evidence/2026-10-22-wall-geometry/wall-comparison.png).

The [length-changing wall experiment](../research/rvt/results/wall-parametric-candidate.md)
extends that profile from 9.5 to 12 feet, with coherent face-local UV changes and fixed
width, height and start point. Independent IFC checks measure 3.39802159104 m³ and
preserve all existing wall meshes. A [separate native BRep audit](../research/rvt/results/wall-brep-audit.json)
reconstructs the saved faces directly and measures a closed 120 ft³ solid, with
6 faces, 12 edges, 8 vertices and consistent saved bounds. Native regeneration
and application acceptance remain unverified.

**Correction to the signature assessment:** Autodesk explicitly documents opening
third-party RVT files through a foreign-file warning. An Autodesk producer signature
is therefore not established as a universal desktop-opening requirement. This does
not identify the 64-byte partition field or validate our unsigned candidates.
[Primary sources and limits](../research/rvt/results/signature_public_sources.md).

Goal: the processing worker delivers a native `.rvt` alongside IFC, written by our own code (no Revit install, no
Autodesk cloud). Status as of 2026-10-22: **complete page framing solved and implemented**. All 917 full pages
and 75 final pages in six licensed fixtures reconstruct byte-for-byte (including
the subsequently identified Contents pages). The expanded historical corpus now verifies 2,760 full and 138 final pages in
eleven files. Nine historical stream layouts require explicit-layout reproduction;
the default encoder selection rule is not universal. Native
element creation and Revit-openability remain under development/unverified; the original
claim that everything else was understood was too strong.

Scripts referenced here are in [`research/rvt/`](../research/rvt/).

Ongoing work is recorded in the [research log](rvt-research-log.md), with
[screenshots and provenance](rvt-evidence/README.md) for reporting.

## Follow-up: trailer solved (2026-10-22)

The trailer is **255 interleaved binary Hamming(2047,2036) codewords** using
`x^11 + x^2 + 1`. The original byte-level probes missed 12 leading and 7 trailing
zero bits. Between them sit 2,805 parity bits = 255 × 11. The payload plus 12
zero bits is exactly 255 × 2,036 bits. All bits are stored LSB-first.

[`paged.py`](../research/rvt/paged.py) implements encoding and strict verification.
[`discover_hamming.py`](../research/rvt/discover_hamming.py) independently recovers
the reciprocal generator by polynomial GCD. [Recorded evidence](../research/rvt/results/README.md)
includes exact reproduction of **509 Core Interior pages + 10 Einhoven pages**,
including schema streams, and byte-identical reconstruction of all 29 eligible
streams. The Python tests cover independent scalar polynomial division over all 255
lanes, boundary lengths, corruption, padding, truncation, and linearity.

This removes the page-parity blocker. It does **not** demonstrate native element
creation or that an edited file opens in Revit. Those require further work and an
external validation oracle. The prior feasibility percentages were subjective,
not measured probabilities.

The original notes below are preserved as the research history. Their proposed
ECC-versus-signature binary test was not decisive: a failed code search cannot
prove a keyed signature. All 509 payload vectors were independent, so a general
whole-page linear fit supplied no evidence either way. Issue #745 concerns
partition reader coverage, not a page-trailer or semantic writer gate.

The follow-up also identified parity on **all 29 short final pages**, contrary
to the original handoff. Their shortened Hamming layouts use generators of
degree 4/5/6/7/9/11. The new [Rust transport crate](../processing/rvt-native/README.md)
verifies all **548 full/final pages**, performs atomic SHA-256-guarded stream
transactions, and refuses stale final-page parity. Its identity write is
whole-file byte identical. A real multipage gzip-header edit re-reads as
byte-identical JSON for all 4,833 elements in rvt-rs. Seven Rust tests cover the
codec, short-page layouts, allocation changes, and failed transactions.

The corrected episode experiment grows `Global/History` from 837 to 845 stored
bytes with fresh parity and preserves all existing episode GUID mappings. The
independent reader emits byte-identical element JSON **and the complete 4.47 MB
IFC export**, including 15,332 IFC GlobalIds. This is not a complete Revit save:
save-counter and other transaction bookkeeping remain unchanged. The two parity
fixtures span Revit **2024 (Core Interior)** and **2023 (Einhoven)**.

### Complete framing follow-up

[Complete codec evidence](../research/rvt/results/complete-codec.md) recovers
exact payload lengths and layout selection, validated on four held-out Revit
2025 models as well as the original 2023/2024 models. The apparent opaque suffix
is page padding plus a bit-count field. A final padded page can occupy a full
65,249 stored bytes; the codecs handle this boundary explicitly. Python and
Rust independently reproduce all 69 streams byte for byte.

The earlier episode experiment above had correct ECC but stale padding-length
metadata. It is superseded by `episode-complete*.json`: both counts and GUID
ordering remain correct, padding is regenerated, and the real payload ends
exactly at gzip EOF. All 4,833 elements remain byte-identical. The IFC output
is identical except for the exporter's two wall-clock timestamps (explicitly
normalized in the recorded comparison). This still does not represent a
complete Revit save transaction.

The Rust writer now accepts `new_payload_file`, allowing stream growth/shrink
without a final-page template. It verifies exact framing and preserves/checks
CFB directory metadata as well as stream hashes. Legacy `new_unpaged_file`
remains available with strict post-write checks.

Remaining: partition/member semantic framing, native element encoders,
reference and save bookkeeping, and an external Revit acceptance check. No
native model exporter is wired into the processing worker. This runtime has
neither usable browser automation nor APS credentials; no Autodesk validation
has occurred.

### Additional partition integrity concern

The [partition audit](../research/rvt/results/partition-audit.md) validates
1,756 explicitly length-framed gzip members in the first segments of 27
partition streams. It also finds a separate 64-byte footer blob in 25 of those
segments, adjacent to Autodesk-generated-data text. Seven ordinary digest
explanations did not match; its purpose and enforcement remain unknown. This
is **not** evidence of a keyed signature, but it is another unresolved field
for native element writing. Later segments, indexes, and references are not
yet completely parsed. The claim that parity was the only blocker is false.

### Complete partition envelope follow-up

[Complete traversal evidence](../research/rvt/results/partition-segments.md)
accounts for every byte of all 27 partition payloads: 523 segments, 3,736
length-framed gzip members, and optional final zero bytes. The new strict
parser/serializer reconstructs each payload exactly. Continuation records
contain byte-sorted GUIDs, not proven editing-episode identifiers. There are
521 nonempty footer blobs, none matching the three tested per-segment
SHA-512 inputs. No repeated inflated segment exists for a determinism test.
This resolves envelope traversal, not footer generation or model semantics.

### First model-parameter edit

The [room-finish experiment](../research/rvt/results/room-finish.md) changes
room 348738 in the MIT RE1 Architecture fixture from `Wood` to `Cork`, updating
its owning object's Adler-32, gzip framing, and page parity. The independent
reader changes exactly one field among 154 elements; its IFC changes exactly
one property after timestamp normalization. Recompression-only and footer-bit
controls preserve all reader elements. These are research candidates: the
unknown footer is not regenerated, save bookkeeping is unchanged, and
Autodesk acceptance remains untested. No element creation is claimed.

### Object-envelope encoders and structural validation

[Object evidence](../research/rvt/results/partition-objects.md) verifies and
re-encodes 736,332 records exactly. Each content group has three matching,
unique ID lists and an empty terminal record; each list's length is its
declared count plus one. All 490,888 applicable Adler-32 values verify.
Whole and split object members are decoded by their explicit framing. The
room edit changes exactly one checksummed object; both matched controls leave
all objects unchanged. These encoders preserve opaque class bodies and do not
supply class-specific model creation or signature generation.

### Signature marker identified from embedded metadata

The [schema binding probe](../research/rvt/results/schema-bindings.md) resolves
the footer's exact wire tag to `SignatureMarker` on all six fixtures. Its
fields are named `m_privateSignature` and `m_publicSignature`. This strengthens
the authentication hypothesis but does not reveal the algorithm, covered
bytes, keying, or enforcement. Content continuation GUIDs map to `ContentKey`.
All identification comes from the files' embedded schema and a pinned public
clean-room reader. Additional unsigned-control candidates clear both signature
fields, using the empty representation seen in two source content groups.
Autodesk acceptance of changed or unsigned nonempty data remains untested.
The local `research/rvt/local/signature-validation.zip` contains the original
and five matched candidates, verified hashes/projections, the fixture MIT
license, and instructions for separate open and save/reopen checks.

## Ground rules

- **Clean-room only.** Work from the bytes of `.rvt` files and from public documentation. Do not disassemble, decompile
  or debug Revit or its DLLs: Autodesk's licence prohibits reverse engineering of the software, and rvt-rs (which we
  build on) follows the same rule (its `CLEANROOM.md`).
- **Test files with clean licences.** Use `2024_Core_Interior.rvt` from magnetar-io's test datasets (MIT; 33,718,272
  bytes, sha256 `c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014`) and Autodesk's public sample
  projects. Do **not** use the Moving Atoms sample RVTs from movingatoms.ai (`Factory_Floor_Revit2027.rvt` etc.): their
  README says they were saved under an Autodesk Education licence, "not for commercial use", and Revit's educational
  flag propagates into derived files.

## What an .rvt is

An OLE / Compound File Binary container. On the Revit 2027 sample (`Linden_Workshop_Revit2027.rvt`, 256 MB) it holds 14
streams: `BasicFileInfo` (UTF-16 text: release, build tag, original path, file GUID), `Contents`, `ProjectInformation`,
`TransmissionData`, `RevitPreview4.0`, `Formats/…` (the class schema), `Global/…` (`Latest`, `ElemTable`, `History`,
`ContentDocuments`, …) and `Partitions/<n>` — 252 MB of the 256 MB is `Partitions/1`, the element data.
`research/rvt/rvtinspect.py` lists streams and prints `BasicFileInfo`.

## Prior art

- **[rvt-rs](https://github.com/DrunkOnJava/rvt-rs)** (Apache-2.0, clean-room, Rust + Python `pip install rvt`), tested at
  commit `b6086d4` / v0.6.1 (2026-10-19): opens Revit 2016–2027, inflates the truncated-gzip streams, decodes
  `Formats/Latest` (all but ~10 field encodings per release), decodes typed element records (best on 2024/2025: 4,833
  elements of Core Interior — 360 walls, 256 columns, 132 doors, 99 floors, 116 rooms), exports IFC4/glTF, and has a
  **byte-preserving stream writer** (`rvt-write`, JSON patch manifests, CFB grow/shrink, GUID/history preservation) and
  a truncated-gzip encoder. Its **field-level semantic writer is "pending"**, gated by ADR-002/ADR-003 until openability
  can be proven. Its own audit lists "ECC validation of the 353-byte tail" and a "paged encoder" as unsolved; see
  [issue #745](https://github.com/DrunkOnJava/rvt-rs/issues/745), [PR #412](https://github.com/DrunkOnJava/rvt-rs/pull/412),
  [PR #695 (Adler-32)](https://github.com/DrunkOnJava/rvt-rs/pull/695).
- **groma** (AGPL): reader only.
- **ODA BimRv SDK** (commercial): writes RVT, latest release only, limited element creation (levels, walls, floors,
  DirectShape). **FME** writes RVT (commercial). Neither publishes the format.
- Jeremy Tammik, ["Reading an RVT file without Revit"](https://jeremytammik.github.io/tbc/a/1407_read_rvt_without_revit.html) (background).

## What our spike did (2026-10-22, ~2 h)

1. Built rvt-rs 0.6.1 (rustc 1.97, all 19 CLIs) and ran `rvt-info`, `rvt-analyze`, `rvt-elements` on Core Interior
   (2024) and Linden Workshop (2027; only Material ×1,229 and GenericModel ×767 decode there).
2. **Original History edit — invalidated by the follow-up audit:** the scratch manifest changed
   count 39 → 40 at offset 0x0e but not the second list count, appended (instead of prepending) an
   episode, and used terminator 0x3f instead of 0x28. Metadata/element re-reading did not validate
   that structure. The old build-tag script also does not apply to the pinned Core Interior fixture.
   The new `episode_experiment.py` changes both counts, prepends a correctly framed GUID, preserves
   existing episode-number mappings and the original 8-byte prefix, and regenerates final-page
   parity. It produces a structurally verified 39 → 40 episode list; both the 4,833-element JSON
   and complete IFC export remain byte-identical through independent rvt-rs reading. It is still
   **not a complete save transaction or Revit-validated output**.
3. **Semantic write that is blocked:** adding an element. That needs `Global/ElemTable` changed (record count at offset
   2, 40-byte records with id/owner on 2024+), and ElemTable is multi-page (~126 KB even in a small project) — so page
   one's trailer must be recomputed. rvt-rs refuses any multi-page re-encode, even an identity one ("spans a
   65249-byte stored page").

## Original blocker (now solved): the 353-byte page trailer

Every `Partitions/*` stream and the large `Global/*` streams are stored in **65,249-byte pages = 64,896 bytes of payload
+ a 353-byte trailer**. The original spike assumed the final short page carried no trailer. **That was wrong:**
the follow-up recovered shortened Hamming parity on every final page in both fixtures.

Observed (`research/rvt/tail_probe.py`, `tail_probe2.py`):
- High entropy, ~7.4 bits/byte; no internal record structure at 8/11/16/22/32/44/88-byte strides; only byte 0 is
  constant (`00`), leaving 352 = 2⁵·11 meaningful bytes.
- Not any common digest of the payload, at either endianness, whole page or per block: CRC-32, CRC-32C, CRC-32/BZIP2,
  CRC-32/MPEG, CRC-64 (ECMA/WE/Jones), CRC-16, CRC-CCITT, Adler-32, xxh32/64/3_64/128, MD5, SHA-1/256/512, BLAKE2b
  (22 variants).
- Consistent with either **forward error correction parity** (computable from the payload alone — e.g. Reed–Solomon
  over GF(256), possibly interleaved) or a **keyed MAC** (not computable without the key).

Other integrity mechanisms found (all reproducible): gzip CRC32 + ISIZE per member; per-data-object Adler-32 inside
partitions; ElemTable record count + records; `Global/History` transaction GUIDs; file GUID and save counter in
`BasicFileInfo`; element counts in `DocumentIncrementTable` and `Global/Latest`. Revit's deflate output is not
byte-reproducible with zlib at any level/memLevel/strategy (likely not required for validity, only for identity tests).
The education-licence flag is not in any plain metadata stream; presumably inside the paged DB streams (not located).

### The next experiment (decides go/no-go)

Determine whether the trailer is **linear in the payload** over GF(2) or GF(256):
1. Collect many full pages (Core Interior has hundreds) as (payload, trailer) pairs.
2. For pages a, b, c with payload(a) ⊕ payload(b) = payload(c) — rare naturally, so instead use the linear-algebra
   form: stack payload bits as rows, trailer bits as targets, and test whether a linear map payload → trailer exists
   (rank / least-squares over GF(2) on a sample of payload bit positions; with 64,896×8 inputs this needs structure —
   start by testing Reed–Solomon hypotheses directly).
3. Reed–Solomon tests: treat the page as codewords of RS(n, k) over GF(2⁸) with common primitive polynomials (0x11d,
   0x12d, 0x14d, 0x187, …), interleaving depths that divide 64,896 and make 352 parity bytes (e.g. 32 interleaved
   codewords × 11 parity, 16 × 22, 11 × 32, 22 × 16, 44 × 8, 88 × 4, 176 × 2), systematic layout with parity
   appended or interleaved; check syndromes = 0 on real pages. A zero-syndrome hit identifies the code exactly.
4. Also test keyed-ness cheaply: two pages with identical payload and different trailers ⇒ keyed/nonce'd (the spike
   found no duplicate payloads to check this).

If it's an ECC: implement the paged encoder, then per-class encoders (Level, Wall, Floor, Column, Pipe, Duct,
DirectShape with categories and parameters) plus ElemTable / Latest / History / increment-table bookkeeping, one
release first (2024 decodes best). If it's keyed: stop — computing it would require extracting a key from Revit, which
is outside clean-room work.

## Validating output without owning Revit

1. **Autodesk Viewer** (viewer.autodesk.com) — free Autodesk ID; upload the `.rvt`; Autodesk's cloud Revit engine
   translates it. Manual but trustworthy "it opens".
2. **APS Model Derivative** (RVT → SVF2) — automatable; needs an APS app (client id/secret); paid API with a monthly
   free tier (pricing changed Dec 2025).
3. **Revit 30-day trial in a Windows VM** — full fidelity incl. audit/repair prompts; evaluation use only.

## Estimate

Before the trailer is resolved: < 15 % chance of Revit-openable output within 2–3 months, and yearly schema churn after
that. If the trailer turns out to be a standard ECC, that rises sharply — the rest is engineering on top of rvt-rs.

## Meanwhile

Customers get IFC4 (Revit opens/links it natively). Legitimate native-RVT routes: Autodesk APS Design Automation for
Revit (Revit engine in Autodesk's cloud, pay per processing hour; a C# app bundle builds native families from our
model) or ODA BimRv.

## Project table and object membership audit

The [element-table codec and audit](../research/rvt/results/element-tables.md)
cover the observed 28/40-byte records, owner chains, History episode ranges,
and partition membership. Embedded schemas identify the trailing allocator
field as `IdentifierSource.m_last`; allocation behavior is not yet proven.
Content-keyed groups must be tracked separately from project-table elements.

## Variable-length object edit

The [object writer](../research/rvt/results/object-writer.md) now rebuilds whole
and split records, compressed members and enclosing partition lengths. A real
room finish grows by 26 bytes; independent full-graph validation preserves all
11 objects and 10 pointer edges except the intended parameter/cursor changes.
All 736,332 corpus records survive repacking. This does not yet implement save
bookkeeping, signature generation or new element creation. The user confirmed
no Autodesk installation or APS account is available for acceptance testing.

## Save bookkeeping audit

[Schema-directed bookkeeping](../research/rvt/results/bookkeeping.md) confirms
that physical increment counts include embedded content, while table partition
IDs are not physical stream ordinals. History offset 14 is the next local
sequence number; it equals the episode count only as an observed invariant.
Explicit modification-episode routing locates 53,527 of 53,544 records; 17
exceptions remain unresolved without a fallback guess. A complete save still
requires correct increment, per-stream revision and signature behavior.

The follow-up selector uses explicit partial-compaction histories for 12 of
those exceptions, including both cases with conflicting bodies. Five have a
sole physical holder but an unexplained historical route. It rejects ambiguous
candidates rather than choosing the greatest stream ordinal; see
[record selection](../research/rvt/results/record-selection.json).

## Save-table codec and additional signature tests

The [save-table codec](../research/rvt/results/save-increments.md) reproduces
844 increment records and 125,144 inflated bytes exactly against independent
schema evidence. Nonempty permutation arrays are explicitly unsupported;
correct revision advancement during a full save is still unproven.

The [signature analysis](../research/rvt/results/signature-analysis.md) rejects
standard canonical raw Ed25519 as a universal explanation in that exact byte
layout and finds no match in 56,268 enumerated digest/coverage comparisons.
Neither finding identifies the actual algorithm or establishes keying.
Both unsigned source groups are empty; unsigned nonempty acceptance is unknown.

## History codec and partition-stream creation

[History serialization](../research/rvt/results/save-history.md) now covers
all observed root/episode fields and guarded prepends, independently checked
against all six files. [Atomic partition creation](../research/rvt/results/transport-create.md)
adds missing numeric streams while preserving existing stream bytes and
metadata. Both are prerequisites; neither constitutes a complete native save.
