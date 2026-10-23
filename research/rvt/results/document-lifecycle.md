# Saved document lifecycle audit

The 100-wall stress candidate has no demonstrated stale document-wide bounding box in the decoded `Global/Latest` graph. This is a bounded negative finding, not proof that Revit will rebuild every necessary index. [Machine-readable evidence](document-lifecycle.json) binds both actual files and the decoder binary.

The complete source graph contains 252 objects and consumes 1,008,502 bytes. The complete stress-candidate graph consumes 1,009,302 bytes with the same 252 objects. Its only semantic object change is `StructuralElemSetTracking.m_elemIdSet`; the 800-byte growth is consistent with the 100 inserted int64 element IDs. The source wall 20826 has exactly one typed ID reference in this Global graph, in that same set.

Recursive field-name inspection finds no `bbox`, `bound`, `extent`, or `outline` field in this graph. `SpatialFieldTracking` contains only its document back-pointer. The only cache-named field is the empty `StructuralConnectionHandlerTypeTracking.m_cacheEntries`. These names do not establish the absence of differently encoded spatial data elsewhere.

`LevelPlanViewTracking.m_levelIdToPlanViewIds` stores level-to-plan-view associations, not wall-instance lists. `SymbolIdMgr` stores default type selections. `ElemsSetWithCellsTracking` does not contain source wall 20826. None is a demonstrated missing registration target for these new instances of an existing type on existing levels. Adding IDs to these structures speculatively would corrupt their measured meaning.

The existing full incoming-reference scan does identify source-specific dependencies outside Global: room 20838 has a `RoomTagPlacement` reference; `LevelRoomPlan` 21258 has `PlanTopology` circuit/segment references; view 132605 has an `AdHocOverrides` map entry. The original wall also occurs in their element-header deletion dependencies. These relationships cannot be cloned indiscriminately to newly placed walls. Current new walls are explicitly non-room-bounding and placed outside source geometry, reducing the demonstrated topology dependency; it does not prove general regeneration behavior.

That historical, hash-bound incoming scan has four unsupported graph records (`DirectShapeType` and `GElement`) and skips 240 embedded content groups. Later compaction-aware coverage improves current-record decoding, but does not retroactively alter the historical report bound here. Neither current-record coverage nor successful independent native/IFC rendering proves Autodesk selection, spatial queries, regeneration, or re-save behavior. Current positive evidence establishes new element geometry and known registration; no additional native field mutation is justified by this audit.

Reproduce from the pinned public-reader probe already built by the registration experiment:

```sh
python3 research/rvt/document_lifecycle_audit.py \
  research/rvt/local/core2024.rvt \
  research/rvt/local/wall-batch-stress-run/verified-candidate.rvt \
  --probe research/rvt/local/new-element-build/target/release/rvt-new-element-probe \
  --result research/rvt/results/document-lifecycle.json
```

The script reads actual CFB streams, verifies full decoded graph consumption, compares semantic objects with pointer offsets removed, and emits field names/hashes rather than private metadata values. The original incoming-reference scan is reused and hash-bound rather than silently represented as a fresh complete scan.
