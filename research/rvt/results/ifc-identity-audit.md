# IFC generated-identifier churn: cause and bounded correction

The 860 changing IFC identifiers come from the public reader's export namespace,
not from changed native room identity. A controlled rerun with the same explicit
namespace removes **all 860 changes**, leaves the unchanged source export
byte-identical, and retains exactly the room-finish and SourceStream changes.
The native-ID maps (85 elements, 2 storeys, 43 types) remain untouched.

## Exact public-source path

Pinned Apache-2 reader commit `b6086d41b9758fd9b92f42f0a47b8345b9c58056`:

- `src/ifc/mod.rs:2002`: `revit_model_global_ids` fills
  `model.global_ids.document` from BasicFileInfo `Unique Document GUID`.
- `src/ifc/step_writer.rs:1228`: that string seeds the generated-ID closure.
- `src/ifc/step_writer.rs:3749`: `stable_guid` hashes
  `b"rvt-rs ifc GlobalId v1\0"`, then the document string, then each role-key
  prefixed with byte `0x1f`; the first 16 SHA-256 bytes receive UUIDv8/version
  bits and are compressed to IFC's 22-character identifier.
- Native element, type and storey IDs come from separate recovered mappings;
  these do not use the document seed when an actual native ID is available.

Independent file evidence shows the BasicFileInfo document GUID equals the
newest History episode in all six fixtures. Consequently it is unsuitable as a
persistent export namespace across the tested append-save transition. The public
reader comment calls it a document identity, but this experiment demonstrates
that changing only that seed explains all observed generated-ID churn. It does
not establish that the candidate is a valid Revit save.

## Our adapter

`ifc_identity_audit.py` compiles a small separate Rust adapter against the clean
pinned reader. It changes only the public `IfcModel.global_ids.document` field,
then invokes the original STEP writer with a fixed timestamp. It does not modify
the reader checkout, alter native IDs, rewrite emitted IFC text, or change RVT.
It emits both default and explicit-namespace controls from the same model.

The namespace is an explicit caller-owned UUID, here the source export's existing
namespace. A production integration must persist one per logical model and define
copy/fork policy. We do not automatically equate History creation GUID with a
universal model identity: copies and forks have not been established. No production
RVT-to-IFC exporter is currently wired in this repository; this is a bounded research
adapter, not a silently changed application behavior.

```sh
python3 research/rvt/ifc_identity_audit.py \
  --reader-source /path/to/pinned/rvt-rs --target /path/to/cached-target \
  --namespace 49409459-71bb-4a7f-9f74-674b7dd20d9d \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/save-candidate-v4.rvt \
  research/rvt/local/ifc-identity-audit-run \
  > research/rvt/results/ifc-identity-audit.json
```

The destination must be new. The JSON binds both inputs, reader commit, adapter
source and complete change classification. v4 is deliberately a control: later
research found stale binary BasicFileInfo duplicates despite its synchronized text
fields. The exporter seed experiment isolates the projection issue independently
of that separate save-metadata defect.
