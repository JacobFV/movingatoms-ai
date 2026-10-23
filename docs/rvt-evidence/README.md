# RVT research evidence archive

This archive records what was implemented, what was tested, and what the
results do **not** establish. The chronological [research log](../rvt-research-log.md)
connects screenshots to commits, commands and machine-readable results.

## Captures

| Capture | Contents | Source revision |
| --- | --- | --- |
| [2026-10-22 baseline](2026-10-22-baseline/manifest.json) | Corpus reconstruction, real room edit, 37-test regression run | `d92645d` |
| [2026-10-22 save/signature](2026-10-22-save-signature/manifest.json) | Save-table codec, signature hypothesis tests, 45-test regression run | `320baea` |
| [2026-10-22 History/transport](2026-10-22-history-transport/manifest.json) | History codec, new-partition transport, 50 Python tests; recorded 14 Rust tests | `cbdc8e0` |

![Corpus reconstruction report](2026-10-22-baseline/corpus.png)

![Real room-edit evidence report](2026-10-22-baseline/room-edit.png)

![Save and signature investigation report](2026-10-22-save-signature/investigations.png)

![History and partition transport report](2026-10-22-history-transport/save-pipeline.png)

These are actual headless Chrome screenshots of **local generated evidence
reports**. They are not Autodesk/Revit screenshots, model renders, or evidence
of Autodesk acceptance. The baseline was captured after the earlier research;
it does not claim to be a screenshot taken during those original experiments.

Every capture directory contains the rendered HTML, PNG screenshots, source
JSON copies, test output, and a manifest with UTC timestamp, source commit,
working-tree state, browser version, commands and SHA-256 hashes. The test run
is fresh; corpus/reader results are previously recorded evidence unless the
log explicitly records a rerun. Local fixture binaries are not copied here.

## Recording subsequent work

For each meaningful implementation or experiment:

1. Add an entry to `docs/rvt-research-log.md`: objective, change, commands,
   observed outcome, limitations, and the relevant commit/evidence paths.
2. Preserve reproducible scripts and machine-readable results in `research/rvt/`.
3. Capture useful visible evidence into a **new** directory; do not overwrite
   historical captures. Label generated reports, actual application screenshots,
   and diagrams accurately. Do not include credentials or private account UI.
4. Review screenshots for cropping/readability and verify their manifest hashes.
5. Commit code and evidence together or in linked incremental commits.

The baseline capture command (choose a new destination for later runs):

```sh
python3 research/rvt/capture_evidence.py docs/rvt-evidence/YYYY-MM-DD-milestone
```

The current generator captures corpus, room-edit, save/signature, and History/transport reports. Extend it
when new milestones need different evidence; do not reuse old results to imply
a new capability. The browser runs with a temporary profile, reading local HTML
without external scripts, fonts or images. The raw reports remain the primary
quantitative evidence; screenshots make them convenient to review and present.

## Coordinated save controls — 2026-10-22

[Manifest](2026-10-22-save-candidate-controls/manifest.json) records source commit
`e96902f`, the dirty-tree changes, exact code/report hashes and the actual Chrome
capture command inputs. [Test log](2026-10-22-save-candidate-controls/tests.txt):
65 Python tests passed during capture. Corpus and Rust results are copied recorded
evidence, not rerun by the screenshot command. Historical save-pipeline panel
retains its original 14-test result; the later Contents correction has 15 Rust tests.

![Four append-save controls and newly identified remaining BFI issue](2026-10-22-save-candidate-controls/save-candidate.png)

The screenshot explicitly records v4's stale binary-header counter/GUID copies,
found after its seven text/Contents relationships passed. These are local
research report screenshots, not Autodesk UI or evidence of Autodesk acceptance.

## Binary identity correction — 2026-10-22

[v5 capture manifest](2026-10-22-save-v5/manifest.json) and
[fresh 74-test Python log](2026-10-22-save-v5/tests.txt) bind this milestone to
commit `0185e31` plus the recorded generator changes. The panel was visually
inspected and the captured artifact hashes verified. It shows all five controls,
the additional binary identity check, and the stable-namespace IFC result.

![v5 binary metadata and stable IFC namespace checks](2026-10-22-save-v5/save-candidate.png)

These are actual screenshots of local research reports, not Autodesk UI.
Subsequent historical corpus additions and page-layout findings are recorded in
the research log; this snapshot retains its original six-file corpus scope.

## Native creation and historical framing — 2026-10-22

[Capture manifest](2026-10-22-native-creation/manifest.json) and
[92-test Python log](2026-10-22-native-creation/tests.txt). Both new panels were
visually inspected; every artifact hash was verified against the manifest.
The corpus/graph results are recorded experiments copied into this capture.

![Registered DataStorage candidate](2026-10-22-native-creation/element-creation.png)

![Historical layout extension across eleven files](2026-10-22-native-creation/historical-layouts.png)

These are local research evidence pages. They do not depict Revit UI or establish
native application acceptance.

## Original source preview audit — 2026-10-22

[Manifest](2026-10-22-source-previews/manifest.json) binds eleven exact extracted
PNG files to their source RVT, stream and image hashes. The contact sheet is an
actual Chrome screenshot, visually inspected. Its pixels are original source
thumbnails, not edited-candidate renders or Autodesk acceptance evidence.

![Eleven original embedded source previews](2026-10-22-source-previews/source-previews.png)

Source attribution: [Magnetar dataset MIT license](../../research/rvt/licenses/magnetar-datasets-MIT.txt)
for Core/Einhoven, [IFC-ECS MIT license](../../research/rvt/licenses/IFC-ECS-MIT.txt)
for RE1. The preview audit records structure and pixel changes separately from
save-counter hypotheses.


### Native wall geometry comparison

[Wall geometry capture](2026-10-22-wall-geometry/manifest.json) records actual IFC mesh
coordinates, triangles, dimensions and source hashes, plotted with Matplotlib and
captured in Chrome. All 360 existing wall meshes remain unchanged. The new wall is
translated 121.92 m along X. This is an independent technical plot, not a Revit UI capture
or proof of native acceptance.

![Independent wall mesh comparison](2026-10-22-wall-geometry/wall-comparison.png)


### Parametric wall length comparison

[Parametric capture](2026-10-22-parametric-wall/manifest.json) compares actual source
and 12-foot candidate IFC meshes at equal scale. It includes source reports, mesh
coordinates, triangles, plot measurements and artifact hashes. The separate native
BRep audit is needed because IFC extrusion can be derived from wall parameters.

![Parametric wall comparison](2026-10-22-parametric-wall/wall-comparison.png)


### Saved native solid audit

[Native BRep capture](2026-10-22-native-brep/manifest.json) adds the independent
native-solid measurement to the IFC comparison. The actual saved candidate has a
closed 120 ft³ solid with six faces, twelve edges and eight vertices. Four open
auxiliary sheets are excluded from volume. Its report and artifact hashes are archived.

![Saved native BRep audit](2026-10-22-native-brep/wall-comparison.png)


### Three walls in one save

[Batch capture and provenance](2026-10-23-wall-batch-corrected/manifest.json) records three
actual IFC meshes at equal scale alongside independent saved-native-solid measurements.
The six-, twelve- and eighteen-foot walls measure 60, 120 and 180 ft³; all existing
native identities and wall meshes remain unchanged. This is a local research report,
not Revit UI or native acceptance evidence.

![Three-wall native and IFC audit](2026-10-23-wall-batch-corrected/batch.png)


### 100-wall stress experiment

[Stress capture](2026-10-23-wall-batch-stress/manifest.json) archives the full reports
and all actual mesh arrays, displaying the first three representative new meshes.
All 100 new native solids pass, totaling 11,940 ft³; all 360 original wall meshes remain
unchanged. The new partition spans ten compressed members.

![100-wall stress result](2026-10-23-wall-batch-stress/batch.png)


### Rotated native walls

[Oriented-wall capture](2026-10-23-oriented-walls/manifest.json) records actual 45°,
90° and −30° IFC meshes alongside independent saved-native-solid measurements.
The reports distinguish ideal native geometry, equivalent IFC local frames and the
exporter's six-decimal placement precision. All prior wall meshes remain unchanged.

![Rotated wall geometry evidence](2026-10-23-oriented-walls/batch.png)


## Minimal project inventory — 2026-10-23

[Manifest and archived source](2026-10-23-minimal-seed/manifest.json) record
the pinned MIT project, complete record coverage and absent building instances.
This is an unchanged-source inventory, not an edited model acceptance test.

![Minimal project inventory report](2026-10-23-minimal-seed/seed.png)


## Variable wall heights — 2026-10-23

[Manifest](2026-10-23-wall-heights/manifest.json) binds full saved-file checks and
actual IFC meshes for8/10/20ft heights with differing lengths and rotations.

![Saved native wall height evidence](2026-10-23-wall-heights/batch.png)


## Minimal native document — 2026-10-23

[Manifest](2026-10-23-seed-walls/manifest.json) binds the complete workflow to
three actual independently triangulated walls in the minimal seed. The report
includes the metadata/native/IFC evidence and explicit validation limits.

![Minimal native document evidence](2026-10-23-seed-walls/candidate.png)


## Named levels and metre-based geometry — 2026-10-23

[Manifest](2026-10-23-named-levels-corrected/manifest.json) binds native and IFC
checks for levels below and above zero, Unicode names and different base/top
constraints. [Initial capture failure](2026-10-23-named-levels/FAILED.md) is retained.

![Named level geometry evidence](2026-10-23-named-levels-corrected/candidate.png)
