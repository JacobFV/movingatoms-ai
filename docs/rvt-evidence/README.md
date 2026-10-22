# RVT research evidence archive

This archive records what was implemented, what was tested, and what the
results do **not** establish. The chronological [research log](../rvt-research-log.md)
connects screenshots to commits, commands and machine-readable results.

## Captures

| Capture | Contents | Source revision |
| --- | --- | --- |
| [2026-10-22 baseline](2026-10-22-baseline/manifest.json) | Corpus reconstruction, real room edit, 37-test regression run | `d92645d` |

![Corpus reconstruction report](2026-10-22-baseline/corpus.png)

![Real room-edit evidence report](2026-10-22-baseline/room-edit.png)

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

The current generator captures the corpus and room-edit reports. Extend it
when new milestones need different evidence; do not reuse old results to imply
a new capability. The browser runs with a temporary profile, reading local HTML
without external scripts, fonts or images. The raw reports remain the primary
quantitative evidence; screenshots make them convenient to review and present.
