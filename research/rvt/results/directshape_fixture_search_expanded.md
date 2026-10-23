# Expanded DirectShape fixture search

Date: 2026-10-22. This extends the initial nine-repository search with eleven
additional repository lookups, focused on IFC import/export examples,
DirectShape tools, and archived exercises. The machine-readable inventory
pins successful tree revisions in
[directshape_fixture_search_expanded.json](directshape_fixture_search_expanded.json).

No Revit 2023/2024/2025 DirectShape instance was established. This is a bounded
negative result, not a claim that no suitable public fixture exists.

## Results of the additional searches

| Repository | Native model result |
| --- | --- |
| Autodesk/revit-ifc | One 2023 project-parameter model; README declares LGPLv2, with no permissive model-specific grant established. Not downloaded. |
| jeremytammik/RoomVolumeDirectShape | No native model path. |
| jeremytammik/DirectObjLoader | No native model path. |
| SpeckleWorks/Revit-Tests | Repository lookup returned 404. |
| DynamoDS/DynamoPrimerNew | Native model inside a licensed exercise ZIP; actual model is Revit 2015. |
| jeremytammik/StlImport | No native model path. |
| teocomi/OBJ-to-DirectShape | No native model path. |
| jeremytammik/SpotElevationTest | Historical `VerySimpleStructuralModel.rvt` path; no modern DirectShape evidence. Not downloaded. |
| ADN-DevTech/aps-revit-ifc-exporter-appbundle | No native model path. |
| autodesk-platform-services/aps-revit.ifc.scheduler | No native model path. |
| yiskang/DA4R-revit-ifc-linker | No native model path. |

Supplemental checks found only the already-audited two Magnetar models and
four RE1 models in their source repositories. Rhino.Inside.Revit's pinned tree
had no archive path naming DirectShape. The inspected Speckle Regression-Testing
tree also had no archive/model path candidate. Search results included recent
forum and issue attachments, but no model-specific permissive grants were
established for them, so no such files were downloaded.

## Archived exercise retained with explicit license

DynamoPrimerNew revision `388bb962bd38e3d77b747d0a84013a49c285e261` includes
an MIT license and `.gitbook/assets/Revit-Creating-DirectShape.zip`. The archive
contains only an RVT input model and a Dynamo workflow. Only the model bytes
were extracted; the workflow was not inspected or executed.

The RVT reports Revit **2015**, build `20140322_1515(x64)`, last saved
2015-07-23. It is an exercise starting point, not evidence of a current
DirectShape instance. The model and license are retained together under
ignored `local/directshape-fixtures/`. Hashes are pinned in the JSON report
and the standalone fetch helper:

```sh
python3 research/rvt/directshape_fixture_archive.py
research/rvt/local/rvt-info \
  research/rvt/local/directshape-fixtures/primer-ARCH-DirectShape-BaseFile.rvt
```

[Model archive](https://github.com/DynamoDS/DynamoPrimerNew/blob/388bb962bd38e3d77b747d0a84013a49c285e261/.gitbook/assets/Revit-Creating-DirectShape.zip),
[MIT license](https://github.com/DynamoDS/DynamoPrimerNew/blob/388bb962bd38e3d77b747d0a84013a49c285e261/LICENSE).

The earlier DynamoRevit singleDirectShape candidate subsequently yielded two
historical instances through separately validated 2015 decoding; see
[the historical graph audit](directshape_legacy_audit.md). Those successful
historical graphs still do not establish defaults for fields introduced later.
No old graph has been relabeled as a 2024 graph.
