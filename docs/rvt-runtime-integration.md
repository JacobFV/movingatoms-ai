# Experimental native RVT runtime integration

The processing worker currently exports IFC4 and GLB. Native RVT research can produce independently audited candidates, but Autodesk opening, regeneration and save acceptance remain untested. Packaging this research does not enable native export by default.

## Current production boundaries

`processing/ma_proc/model/build.py` computes model geometry once and returns GLB, graph/index JSON and IFC. Its explicit experimental option additionally stages an RVT and JSON evidence report before any upload. Both are registered deliverables linked through file metadata, leaving the revision database/API `ifc_key` and `glb_key` schema unchanged. Revision notes and file blocks describe the native artifact as experimental, with opening/regeneration unverified.

`geometry.element_parts` catches exceptions and returns no parts; `all_parts` omits those elements. This is acceptable only as the existing renderer's behavior, not an RVT completeness contract. A native adapter must compare every live nonlevel model ID against explicit exported parts, reject unsupported/missing geometry and unknown categories, preserve all mesh parts, and describe intentional treatment of openings and other non-drawable concepts. The strict production request adapter addresses this boundary. Geometry is already world-space metres and Z-up; applying another local transform would be incorrect.

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

Reader source revision `b6086d41b9758fd9b92f42f0a47b8345b9c58056` is **Apache-2.0**, including its NOTICE. The published ricaun seed is MIT licensed, with the pinned license text retained. olefile has its own copyright/license text and must retain it. The transport Cargo manifest declares MIT; this repository does not currently provide a separate transport LICENSE text. The bundle includes that declaration and explicitly records the limitation rather than inventing a copyright notice. The bundle also retains actual license/notice alternatives for every resolved host Cargo dependency plus installed Rust standard-library/toolchain inventories; these are bound by the payload manifest. The first-party transport declaration is preserved without inventing a copyright attribution.

## Invocation and publication contract

The intended offline command is:

```sh
python /path/to/bundle/run.py \
  --request explicit-model-request.json \
  --output new-run-directory \
  --acknowledge-hypotheses
```

The launcher validates payload hashes, pinned sources, binary architecture and compatible-host constraints before importing authoring code. Explicit prebuilt probe objects replace research-only runtime compilation. Every run binds source/candidate hashes across transport, metadata and independent native/graphics reports. Only a successful audited run publishes `verified-candidate.rvt`; failures retain a failed report without presenting a verified result. Destination paths are no-clobber.

The implemented worker option calls the adapter before publication and stages all six artifacts before upload. Requested native output failure marks the revision as an error and publishes no files. IFC/GLB remain the default; normal checkpoints do not invoke the runtime. The agent tool forwards native flags only when explicitly selected and acknowledged, while preserving legacy calls.

## Container build path

Build the standalone bundle outside the production Docker context, or add a narrowly defined packaging context. Compile the Rust transport and three probes for each target architecture in a build stage. The current Dockerfile cross-compiles Potree and installs target Python wheels without executing foreign binaries; native Rust builds must preserve that design, supplying Rust target libraries and the correct target linker. The first bundle builder is host-architecture-only; cross-architecture packaging is a separate explicit implementation task.

Copy only the verified bundle into the final image and run under existing UID10001 with scratch files under writable `/work`. Do not download fixtures, compile probes, access git, or install packages during a job. Tests cover successful output, missing geometry, malformed metadata, source/profile and binary integrity, architecture/libc mismatch, no-clobber and audit failure. The processing CLI can exercise the bundle without changing default build behavior.

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

Earlier hardened bundle: `research/rvt/local/runtime-bundle-v2` (ignored generated artifact),81 hashed payloads,56 reachable Python modules,15,898,620 payload bytes. Manifest SHA256: `1c59b4593435f9e3a8f4c84f43e8b2d5d1574693685d2c708ec1a74de3834166`. It contains only the allowlisted six profiles and one licensed seed. All four executables are aarch64; the strongest measured libc requirement is glibc2.35, with libc, libm and libgcc_s SONAME checks. Python3.12 is required.

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
  --bundle research/rvt/local/runtime-bundle-v4 \
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


## Worker deployment and opt-in job contract

Configure `MA_RVT_RUNTIME_BUNDLE=/opt/movingatoms/rvt-runtime` in the worker's
`/etc/movingatoms/worker.env`. Mount a verified, compatible-host bundle read-only
at that path in the worker container, for example an additional Docker volume
`/opt/movingatoms/rvt-runtime:/opt/movingatoms/rvt-runtime:ro`. The existing service
mounts `/var/lib/movingatoms` at `/work`; keep runtime assets separate from writable
job scratch. The normal Python3.12 worker interpreter launches the bundle.
Building and testing a bundle does not deploy it or configure production hosts.

The build job input is explicit:

```json
{
  "title": "Experimental native checkpoint",
  "experimental_native_rvt": true,
  "acknowledge_native_hypotheses": true
}
```

`publish_revision` exposes both booleans and keeps them false for ordinary
checkpoints. Acknowledgment already given in the conversation is honored. A
missing runtime, nonboolean flag, missing acknowledgment, missing geometry or
failed native audit prevents publication. Successful native builds add
`model.experimental.rvt` and `model.experimental.validation.json`; both file
records carry experimental qualification and the RVT record links its evidence.

A real worker run against an in-memory API (no external publication) passed with
10 model elements and 312 saved triangles. Six staged artifacts became four
registered deliverables. Candidate SHA:
`96677553b237e357d5b69b39426670641a05248156dcefe8d93365bd819d4660`.
This differs from the standalone control because the worker includes the project
ID in preserved source model metadata. [Worker evidence](../research/rvt/results/seed-model-worker.json).

Validation: 54 Python adapter/export/model/job tests, five agent routing tests,
and `npx tsc --noEmit -p workers/realtime/tsconfig.json` pass. Failure tests check
that native errors cause zero uploads, file registrations, chat messages or model
base updates. No application compatibility is inferred from these worker tests.


## Final packaged runtime (v4)

Use `research/rvt/local/runtime-bundle-v4` for subsequent runs. It contains 254
hash-bound payloads (32,468,943 bytes), including actual notices for 74 resolved
Rust dependency packages and 170 dependency/toolchain license evidence files.
There are no missing toolchain notice files. The probe Cargo lockfile is checked
in as `research/rvt/runtime-probes.Cargo.lock`; both native builds now use
`--locked --offline`. Rebuilds cannot silently select newer cached dependencies.

[Manifest and package evidence](../research/rvt/results/runtime-bundle-v4.json)
record the manifest SHA
`a366584f41e9208609e0d089bc4c3b01dfde57e7e320879db86c7e57f9d9b349`.
The generated distributable archive is
`research/rvt/local/ma-rvt-native-runtime-aarch64-v4.tar.gz` (5,881,942 bytes), SHA
`16509874612f550308320bac4fd91f7b050ece472a45193abe6b2786265254dd`.
Host requirements remain Linux aarch64, Python3.12, glibc≥2.35 and the recorded
library SONAMEs. Other architectures require rebuilding on a compatible host.

The final offline run under `env -i PATH=/nonexistent /usr/bin/python3 -S`
reproduces the processing-model candidate SHA
`47a3e82c61b45d85cde909ffde43d8a53da01c4e403bba2a10d9a81f0232ccf7`.
The complete research suite now passes 309 tests. Historical v1/v2 runs and their
captures remain unchanged; v3 added notice collection and v4 pinned the lockfile.
