# Experimental native RVT runtime integration

The processing worker currently exports IFC4 and GLB. Native RVT research can produce independently audited candidates, but Autodesk opening, regeneration and save acceptance remain untested. Packaging this research does not enable native export by default.

## Current production boundaries

`processing/ma_proc/model/build.py` computes model geometry once and returns GLB, graph/index JSON and IFC. Its upload/content-type list, revision notes and chat file blocks only know those formats. The revision database/API has `ifc_key` and `glb_key`, with no `rvt_key`; a separate registered deliverable and JSON evidence report can be added without immediately changing the revision schema. Existing messages saying native RVT cannot be produced would need qualified wording if an experimental output path is explicitly selected.

`geometry.element_parts` catches exceptions and returns no parts; `all_parts` omits those elements. This is acceptable only as the existing renderer's behavior, not an RVT completeness contract. A native adapter must compare every live nonlevel model ID against explicit exported parts, reject unsupported/missing geometry and unknown categories, preserve all mesh parts, and describe intentional treatment of openings and other non-drawable concepts. Root's separately owned production request adapter addresses this boundary. Geometry is already world-space metres and Z-up; applying another local transform would be incorrect.

The generic seed writer stores meshes as DirectShape, not native editable walls/families. Requested levels and properties are retained in application extensible-storage metadata; DirectShape's native associated-level field remains the measured unset sentinel. Per-part geometry is checked after declared float32 quantization. Category appearance uses measured seed styles; source material appearance and semantic family behavior must not be promised by the model adapter.

## Packaging gaps and proposed runtime

The current processing Docker build context copies only `ma_proc`, dependency metadata and PotreeConverter. It contains no RVT transport executable, public-reader probes, seed fixture, evidence profiles or research Python modules. Its dependencies omit `olefile`. Copying `research/rvt` wholesale would include unrelated fixtures and local outputs and would leave runtime git/cargo compilation dependencies.

The standalone bundle is deliberately separate:

- `runtime/`: explicit AST-reachable local Python modules, the three audited probe Rust source files used for hash binding, and vendored pure-Python olefile.
- `runtime/results/`: only `seed_save_context.json`, `seed_level-profile.json`, `seed_categories.json`, `directshape-mesh-profile.json`, `directshape_legacy_audit.json`, and `directshape_current.json`.
- `assets/minimal-seed.rvt`: only the licensed 434,176-byte seed, SHA256 `674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe`.
- `bin/`: transport, properties probe, independent index probe and independent scene probe, compiled at bundle-build time against the pinned reader. No compiler or reader checkout is needed at use time.
- `notices/`, build lockfile provenance and a complete payload hash manifest.

The initial authoring closure measured47 modules/300,861 bytes; adding the orchestrator, independent verifier and bundle utility expands it to56 modules (the generated manifest is authoritative). Six profile files total1,934,317 bytes. The measured local properties probe is approximately2MiB and transport916KiB; rebuilt binary sizes and architecture are recorded per bundle. The build host is Linux aarch64; that is not a portable binary for amd64, macOS or every Linux libc version.

Reader source revision `b6086d41b9758fd9b92f42f0a47b8345b9c58056` is **Apache-2.0**, including its NOTICE. The published ricaun seed is MIT licensed, with the pinned license text retained. olefile has its own copyright/license text and must retain it. The transport Cargo manifest declares MIT; this repository does not currently provide a separate transport LICENSE text. The bundle includes that declaration and explicitly records the limitation rather than inventing a copyright notice. Dependency lockfiles are provenance, not a substitute for a release-wide third-party license review.

## Invocation and publication contract

The intended offline command is:

```sh
python /path/to/bundle/run.py \
  --request explicit-model-request.json \
  --output new-run-directory \
  --acknowledge-hypotheses
```

The launcher validates payload hashes, pinned sources, binary architecture and compatible-host constraints before importing authoring code. Explicit prebuilt probe objects replace research-only runtime compilation. Every run binds source/candidate hashes across transport, metadata and independent native/graphics reports. Only a successful audited run publishes `verified-candidate.rvt`; failures retain a failed report without presenting a verified result. Destination paths are no-clobber.

A future worker integration should be opt-in, call the adapter before publication, stage artifacts in its per-job work directory, and upload an explicitly experimental RVT plus its evidence report only after the offline runtime succeeds. If explicitly requested native output fails or cannot represent an element, return an actionable failure; never silently substitute partial native output. IFC/GLB remain supported deliverables. Building a normal model must not silently invoke the experimental runtime.

## Container build path

Build the standalone bundle outside the production Docker context, or add a narrowly defined packaging context. Compile the Rust transport and three probes for each target architecture in a build stage. The current Dockerfile cross-compiles Potree and installs target Python wheels without executing foreign binaries; native Rust builds must preserve that design, supplying Rust target libraries and the correct target linker. The first bundle builder is host-architecture-only; cross-architecture packaging is a separate explicit implementation task.

Copy only the verified bundle into the final image and run under existing UID10001 with scratch files under writable `/work`. Do not download fixtures, compile probes, access git, or install packages during a job. Add end-to-end tests for successful complete output, unsupported/missing element geometry, malformed metadata, wrong seed/profile hashes, altered binaries, architecture/libc mismatch, no-clobber and audit failure before exposing a worker switch. The processing CLI can exercise the bundle without changing default build behavior.

## Bundle build and compatible-host checks

The build command is offline once the pinned Rust dependency cache and licensed seed are present:

```sh
python3 research/rvt/build_runtime_bundle.py build NEW_BUNDLE \
  --reader /path/to/pinned/rvt-rs \
  --seed research/rvt/local/minimal_seed-Project.rvt \
  --cache research/rvt/local/runtime-bundle-cache \
  --olefile-license /usr/share/doc/python3-olefile/copyright
python3 NEW_BUNDLE/runtime/build_runtime_bundle.py verify NEW_BUNDLE
```

The package tool builds all four binaries itself, records probe source/binary hashes and dependency lockfiles, and refuses an existing destination or source changes during compilation. The olefile license path is explicit because installed package layouts differ; its exact text and vendored module bytes are hashed in the manifest.

Host validation requires Python3.12, Linux, the matching ELF machine, and glibc at least as new as the maximum required version found in each binary's versioned symbols. Build-time `readelf` records DT_NEEDED library SONAMEs; the runtime checks those plain SONAMEs can be loaded. This is a measured compatible-host contract, not an assertion that the bundle runs on arbitrary Linux distributions. Initial tests cover malformed ELF, too-old glibc, non-glibc hosts, path-bearing library names, altered/missing payloads, nested manifest files, unexpected bytecode, symlinks and existing destinations.

Only the root manifest is excluded from payload inventory; unchecked bytecode caches are not allowed. The launcher disables bytecode writes before importing bundled modules. Hashes detect corruption against the supplied manifest; they are not a digital signature or a claim that a manifest from an untrusted party is authenticated.

## Completed standalone bundle measurement

Final hardened bundle: `research/rvt/local/runtime-bundle-v2` (ignored generated artifact),81 hashed payloads,56 reachable Python modules,15,898,620 payload bytes. Manifest SHA256: `1c59b4593435f9e3a8f4c84f43e8b2d5d1574693685d2c708ec1a74de3834166`. It contains only the allowlisted six profiles and one licensed seed. All four executables are aarch64; the strongest measured libc requirement is glibc2.35, with libc, libm and libgcc_s SONAME checks. Python3.12 is required.

The official `results/seed-model-request.json` ran successfully with site packages disabled and no tools on PATH:

```sh
env -i PATH=/nonexistent /usr/bin/python3 -S \
  research/rvt/local/runtime-bundle-v2/run.py \
  --request research/rvt/results/seed-model-request.json \
  --output research/rvt/local/runtime-bundle-smoke-v2 \
  --acknowledge-hypotheses
```

The independently verified output SHA256 is `56b5b5274c3f75681e5884d84424fc1678f9f63f308accc317e2c8373a9ca8c5`, exactly matching the source-checkout pipeline. Its run-report SHA256 is `b62c8865031febd607a3042ae9fd4b39813173e62dfc4726eb0001ef967444c2`. This run used no git, cargo, reader checkout or installed site packages; olefile came from the validated bundle. Five focused test methods cover the closure, no-clobber, corruption/inventory, symlink, architecture and libc checks. The earlier v1 bundle remains an immutable evidence control; v2 additionally rejects unlisted symlink directories and requires a dependency check entry for every binary.

## Processing model command

The implemented offline processing command converts a saved model-read JSON into
an explicit request and calls the verified runtime. It preserves exact source
records and level/type/model context in bounded metadata. It rejects missing
geometry and unsupported opening semantics before launching the writer.

```sh
PYTHONPATH=processing processing/.venv/bin/python -m ma_proc.model.rvt_export \
  research/rvt/results/seed-model-production-input.json \
  --bundle research/rvt/local/runtime-bundle-v2 \
  --output NEW_OUTPUT_DIRECTORY \
  --runtime-python /usr/bin/python3 \
  --acknowledge-hypotheses
```

For mesh-backed source elements, supply `--mesh-directory` containing local
`SHA256.glb` assets; the command checks their content hashes. The processing
Python environment needs the normal model geometry dependencies. The runtime
Python process needs only its measured host requirements and bundled dependencies.
The full ten-element room control and exact source recovery are documented in
[the production-model report](../research/rvt/results/seed-model-production.md).
