# Writing native Revit (.rvt) without Revit — research notes

Goal: the processing worker delivers a native `.rvt` alongside IFC, written by our own code (no Revit install, no
Autodesk cloud). Status as of 2026-10-22: **blocked on one unknown, the 353-byte page trailer** (below). Everything
else needed for a writer is understood or already built in open source.

Scripts referenced here are in [`research/rvt/`](../research/rvt/).

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
2. **Semantic write that worked:** on the single-page `Global/History` stream, inflate → append one transaction GUID
   entry and bump the entry count 39 → 40 → re-encode → `rvt-write`. rvt-rs re-reads it; file GUID, save counter (66)
   and all 4,833 elements unchanged. `research/rvt/hist_patch.py` builds that kind of patch manifest. Caveat: Revit's
   8-byte stream prefix there is `01 00 00 00 00 00 00 00`; rvt-rs's `CustomPrefix8` framing writes 8 zero bytes, so
   even this edit is not yet faithful to Revit's own framing. **Not validated by Revit.**
3. **Semantic write that is blocked:** adding an element. That needs `Global/ElemTable` changed (record count at offset
   2, 40-byte records with id/owner on 2024+), and ElemTable is multi-page (~126 KB even in a small project) — so page
   one's trailer must be recomputed. rvt-rs refuses any multi-page re-encode, even an identity one ("spans a
   65249-byte stored page").

## The blocker: the 353-byte page trailer

Every `Partitions/*` stream and the large `Global/*` streams are stored in **65,249-byte pages = 64,896 bytes of payload
+ a 353-byte trailer**. The final, short page of a stream carries no trailer.

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
