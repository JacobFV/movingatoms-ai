# DirectShape instance fixture search

Date: 2026-10-22. No Revit 2024 DirectShape **instance** was established in this
bounded public-repository search. Two permissively licensed candidates were
retained, with different useful outcomes. No proprietary Revit implementation
was inspected or executed.

## Dynamo singleDirectShape: useful historical candidate, not 2024

The DynamoRevit `Revit2024` branch contains
`test/System/DirectShape/singleDirectShape.rvt`. Its branch revision
`c2dcaf5da0726b8643b6065815aa2c2c33d828b8` has no conventional license file.
Rather than infer a grant from GitHub metadata, the same exact Git blob
`c502fd22e53303c8065f13c7e533b9b44e790069` was found at the same path on master
revision `49cd43c5c3b21271640ae043b8b77374e4796843`, alongside an explicit
Apache-2.0 `LICENSE.txt`. Both model and license were downloaded from that
licensed revision and hashed.

The file metadata reports Revit **2015**, build `20140322_1515(x64)`, saved
2015-08-26. The native graph probe refuses this version because its object
framing is not validated. This refusal is retained; no 2024 layout was forced
onto old bytes. The filename is a promising instance clue, not a verified
current-instance graph. The historical candidate was handed to the geometry
research worker for separately validated decoding.

- Model SHA-256: `3b05630eb71230b567b891f7829a9a6326b435b002b99d571d3830790fe50431`
- License SHA-256: `ec1fe45049abf566d3e86f51ce815c1fd52de7c3095eeef71f72fb5c144f837d`
- [Pinned model](https://github.com/DynamoDS/DynamoRevit/blob/49cd43c5c3b21271640ae043b8b77374e4796843/test/System/DirectShape/singleDirectShape.rvt)
- [Pinned license](https://github.com/DynamoDS/DynamoRevit/blob/49cd43c5c3b21271640ae043b8b77374e4796843/LICENSE.txt)

## Ricaun 2024: small project, no DirectShape

The MIT-licensed `ricaun-io/ricaun.Revit.FileInfo` revision
`9228ef12063fd294a565c47b989449ab93460a61` includes a 434,176-byte Revit 2024
project fixture. The current-record probe succeeds, sees 2,300 indexed elements,
and selects zero DirectShape or DirectShapeType records. It is a useful small
2024 project but does not meet the requested instance requirement.

- Model SHA-256: `674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe`
- License SHA-256: `47479541ef4e0cef78174f121d2408cd9ea4a9c3182ff2699eb0c002943b23f8`
- [Pinned model](https://github.com/ricaun-io/ricaun.Revit.FileInfo/blob/9228ef12063fd294a565c47b989449ab93460a61/ricaun.Revit.FileInfo.Tests/Files/2024/Project.rvt)
- [Pinned license](https://github.com/ricaun-io/ricaun.Revit.FileInfo/blob/9228ef12063fd294a565c47b989449ab93460a61/LICENSE)

## Other inspected trees

Speckle's sharp, sharp-connectors and Regression-Testing repositories had no
RVT/RFA/RTE paths in the inspected trees; xUnitRevit contained only `walls.rvt`.
Rhino.Inside.Revit had older documentation projects and version-specific
blank templates, including 2024. Jeremy Tammik's MIT DirectShapeFromFace
repository had a historical test RVT; it was not downloaded after the newer
Dynamo branch proved misleading. The direct-shape-framework tree had no native
model files. Repository revisions, paths and any lookup errors are recorded in
[directshape_fixture_search.json](directshape_fixture_search.json).

## Reproduce and retain

```sh
python3 research/rvt/directshape_fixture_fetch.py
research/rvt/local/rvt-info research/rvt/local/directshape-fixtures/singleDirectShape.rvt
/tmp/rvt-wall-candidate-target/release/rvt-directshape-probe \
  research/rvt/local/directshape-fixtures/singleDirectShape.rvt
/tmp/rvt-wall-candidate-target/release/rvt-directshape-probe \
  research/rvt/local/directshape-fixtures/ricaun-Project2024.rvt
```

The 2015 probe is expected to return exit 1 with an unvalidated-framing error.
The probe source is `research/rvt/directshape_probe.rs`; the temporary binary
must be rebuilt if cleared. The fetch helper checks model and license hashes,
retains them together under ignored `local/directshape-fixtures/`, and never
overwrites mismatched files. Search inventory can be refreshed with
`python3 research/rvt/directshape_fixture_search.py`; branch tips may change,
so the candidate report and downloader retain fixed revisions independently.

Machine-readable outcomes are in
[directshape_fixture_candidates.json](directshape_fixture_candidates.json).
