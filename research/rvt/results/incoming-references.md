# Incoming references to the creation source profiles

Pinned `core2024.rvt` SHA-256:
`c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014`.
Independent public reader revision:
`b6086d41b9758fd9b92f42f0a47b8345b9c58056`.

The read-only audit scans **79,275 current project records** (26,425 indexed
elements, channels 101/102/103) for signed little-endian 64-bit encodings of
DataStorage **80437** and wall **20826**, then decodes only the 13 matching
bodies using the file's embedded schema and the independent public reader.
All 13 consume their entire bodies. No candidate graph remains unresolved.
Selection uses 79,245 exact episode routes and 30 unique explicitly linked
compaction-history routes; there are no unresolved routes and no highest-holder
fallback. The physical scan checked 85,680 historical/current base-group records;
46 embedded content groups are outside the project-ID domain and excluded.

## External typed ElementId references

| Referencing element | Channel | Embedded-schema field path | Target |
|---|---|---|---|
| 20838, RoomElem | 101 | ElementParents.m_deletion[3] | wall 20826 |
| 20838, RoomElem | 102 | RoomTagPlacement.m_ref1 | wall 20826 |
| 21258, LevelRoomPlan | 101 | ElementParents.m_deletion[47] | wall 20826 |
| 21258, LevelRoomPlan | 102 | PlanTopology.m_segments[152].m_key.m_item.m_linkInstOrHostId | wall 20826 |
| 21258, LevelRoomPlan | 102 | PlanTopology.m_circuits[13].m_sides[2].m_item.m_linkInstOrHostId | wall 20826 |
| 21258, LevelRoomPlan | 102 | PlanTopology.m_circuits[14].m_sides[2].m_item.m_linkInstOrHostId | wall 20826 |
| 132605, DBView3d | 101 | ElementParents.m_deletion[76] | wall 20826 |
| 132605, DBView3d | 102 | AdHocOverrides.m_elementMap[46].first | wall 20826 |

No other current project record contains a decoded inline **ElementId** reference
to DataStorage 80437 within this scan's domain. Its own header deletion list and
body identity contain its ID. The wall likewise has self-references. These are
separate from Global/Latest registration lists audited by the creation work.

Element 130286 initially exceeded the reader's default 100,000-value budget.
A bounded second attempt at 2,000,000 values also refused both candidate bodies.
The final 10,000,000-value / 500,000-object bounds decode them completely:

- Channel 102, DirectShapeType: 15,639,178 bytes, 144,380 graph objects.
- Channel 103, GElement: 16,514,325 bytes, 172,317 graph objects.

Their numerical matches occur in geometry-history keys/IDs, GInfo tags and graph
pointer tokens; there are no typed ElementId matches. The JSON records diagnostic
numeric paths separately, including decoder pointer-offset metadata, so these
are not misrepresented as element references. The source wall's own GElement
also stores its identity as a scalar `m_elementId`, illustrating why this audit
does not claim all references have the ElementId wrapper.

## Creation implications and limits

A new, translated wall leaves the old wall intact. Existing room placement,
source-wall view overrides, and deletion dependencies must not be blindly
retargeted or copied to the new wall. The LevelRoomPlan contains saved room
boundary/topology relationships; registering a new wall in Global/Latest alone
does not establish that derived room topology has been correctly recomputed.
This audit identifies that remaining concern; it does not implement a geometric
room-boundary evaluator or prove Autodesk acceptance.

The byte prefilter covers only raw signed 64-bit little-endian encodings. It
cannot rule out alternative encodings, opaque caches, external references,
embedded-content IDs, or application invariants not represented as ElementId
fields. Typed traversal follows embedded-schema inheritance and inline class
references, including arrays; graph pointer targets are examined as separate
objects. Numeric coincidences are not promoted to semantic references.

## Reproduction

```sh
python3 research/rvt/incoming_references.py research/rvt/local/core2024.rvt \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  --target research/rvt/local/new-element-build/target \
  --catalog research/rvt/local/new-element-catalog.json \
  > research/rvt/results/incoming-references.json
python3 -m unittest discover -s research/rvt -p test_incoming_references.py
```

The report binds the source file, embedded schema, catalog bytes, source reader
revision, and each candidate body by hash. Two focused traversal tests pass,
covering inheritance, typed arrays, pointer separation, numeric lookalikes,
target exclusion and inheritance cycles. No fixture or proprietary code is
modified or committed by this audit.
