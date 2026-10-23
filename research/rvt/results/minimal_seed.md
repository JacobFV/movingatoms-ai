# Minimal native seed audit

**Preferred research seed: `ricaun.Revit.FileInfo.Tests/Files/2024/Project.rvt`.**
It is a real Revit 2024 project, 434,176 bytes, with a single base partition and
no decoded building-instance classes. It avoids inheriting Core Interior's
building and does not require converting a template to a project.

The [source repository](https://github.com/ricaun-io/ricaun.Revit.FileInfo/tree/9228ef12063fd294a565c47b989449ab93460a61)
publishes it under its [MIT license](https://github.com/ricaun-io/ricaun.Revit.FileInfo/blob/9228ef12063fd294a565c47b989449ab93460a61/LICENSE)
(Copyright 2023 ricaun). The repository-level license and fixture are pinned;
no additional file-specific license or exclusion was found. This is evidence
for using the published fixture, not an assertion about the original author's
Revit subscription edition.

- Source commit: `9228ef12063fd294a565c47b989449ab93460a61`.
- Fixture SHA-256: `674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe`.
- License SHA-256: `47479541ef4e0cef78174f121d2408cd9ea4a9c3182ff2699eb0c002943b23f8`.
- Download: [Project.rvt, pinned](https://raw.githubusercontent.com/ricaun-io/ricaun.Revit.FileInfo/9228ef12063fd294a565c47b989449ab93460a61/ricaun.Revit.FileInfo.Tests/Files/2024/Project.rvt).
- Ignored local path: `research/rvt/local/minimal_seed-Project.rvt`.

## Independent inventory

The pinned public reader `b6086d41b9758fd9b92f42f0a47b8345b9c58056` decodes all
**6,900 current records for 2,300 indexed elements**, across channels 101/102/103.
Every graph consumes its complete body. There are **zero unsupported graphs,
zero records outside the exact revision route, and zero selected IDs without
records**. No highest-holder fallback contributes to this result.

The complete class inventory is in `minimal_seed.json`. It includes one Level,
one BasicWallType, two ProjectPhases, 33 MaterialElem records, one DBViewPlan,
23 LegendComponent records, and document/settings/type scaffolding. SWall,
RoomElem, FamilyInstance, CurveElem, ImportInstance, DirectShape and
DirectShapeType are absent. The seed is not literally an element-free database;
its built-in document scaffolding must be retained and understood.

Useful seed identities:

| Class | Element ID |
|---|---:|
| ProjectPhase, Existing | 1 |
| ProjectPhase, New Construction | 4 |
| Level | 1916 |
| BasicWallType | 1947 |

Existing strict research codecs accept this fixture's History,
DocumentIncrementTable, ElemTable and partition object framing. Its sole
`Partitions/0` has root tag `0x37b`, 2,300 objects per channel, and one base group
with no embedded content groups. The existing Rust transport verifier checks
13 streams, four full parity pages and nine final pages, preserving the source
hash exactly. This verifies storage framing, not Revit acceptance of edits.

## Other candidates and search coverage

| Candidate | Published license | Native result | Decision |
|---|---|---|---|
| ricaun `ProjectTemplate.rte` | MIT | 2024; 2,300 elements, 6,900 complete graphs, no off-route records | Useful paired control; prefer its `.rvt` sibling |
| Udaragithub `PDS-template_v1.rte` | MIT | 2024; 7,184 elements, 20,788 complete / 764 unsupported graphs | More complex template, not preferred |
| DynamoRevit `Empty-Metric.rvt` | Apache-2.0 | 2017; metadata readable, native graph inventory explicitly rejects this version | Outside current writer profile |

All four candidates, license bytes and downloads are hash-pinned in
`minimal_seed.py`; reports include their immutable URLs. The corresponding
license files are archived alongside this report. Model binaries remain ignored.

The preferred template sibling has SHA-256
`5dfe764e2c47aabb7e55c02d3b1bd53370f38088c8db2af5a68224dd82a79364`.
Its metadata shares the project's document GUID and was saved 12 seconds later;
that is potentially useful paired-save evidence, not proof that merely renaming
an `.rte` creates a valid project.

The pinned magnetar dataset tree contains only the two already-used populated
projects (plus families), so it offers no empty project seed. Additional public
repository-tree searches covered DynamoRevit, RevitTestFramework, Speckle's two
connector repositories, ricaun.RevitTest, phi-ag/rvt, Reveche, RevitLookup and
RevitDBExplorer. The tiny rvt-rs tier-1 samples are synthetic scaffolds, not
eligible substitutes for real Revit-generated projects. Searches inspected
public file lists, license texts and model bytes only; no Revit proprietary
code was accessed.

## Next implementation boundary

The small `.rvt` provides a credible route to producing a requested model without
retaining a donor building. It does **not** by itself make the existing
Core-based wall encoder portable: wall type, level, material, phase, document
references, schema compatibility and every copied geometry dependency must be
resolved against this seed. New object registration and save bookkeeping still
need the existing guarded mutation pipeline. Signature acceptance, cache
regeneration and Autodesk opening remain unvalidated. No seed was modified in
this audit.

## Reproduce

```sh
python3 research/rvt/minimal_seed.py \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  --target research/rvt/local/new-element-build/target \
  > research/rvt/results/minimal_seed.json
python3 -m unittest discover -s research/rvt -p test_minimal_seed.py
processing/rvt-native/target/release/ma-rvt-native verify \
  research/rvt/local/minimal_seed-Project.rvt
```

Two provenance tests pass: immutable pins for every fixture/license and rejection
of a mismatched local cache without overwriting it. The inventory helper builds
against the pinned clean public reader and does not modify its checkout.
