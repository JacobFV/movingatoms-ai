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
