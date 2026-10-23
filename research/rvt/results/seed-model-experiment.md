# Verified saved model pipeline

The complete combined control and large indexed-surface control passed the
transport, save-metadata and independent native-reader audits under frozen
commit534845a. Both were published with no-clobber hard links only after every
report bound the same source and candidate SHA. All2,300 prior native identities
and original partition streams remained unchanged.

| Run | Saved content | Candidate SHA-256 |
|---|---|---|
|baseline|3 named levels (-3,0,7m),3 DirectShape elements,17 triangles across4 primitives|56b5b5274c3f75681e5884d84424fc1678f9f63f308accc317e2c8373a9ca8c5|
|large|33,000 vertices,11,000 triangles,2 indexed mesh primitives|4c781aa92a5d42a1124c862a937b44cebbb8175aeae394c988cfb236345407e7|

The baseline includes a wall-category closed cuboid, generic multipart open
panels and roof-category sloped surface, nested JSON properties and Unicode
names. Requested level relationships are persisted in our own ExtensibleStorage
metadata; DirectShape native associated-level remains-1. The two new native
levels are independently checked; requested Level1 at0m reuses the seed level.
Category/style/material IDs are measured seed context, with explicit material
bindings in the native geometry.

The independent verifier derives expected geometry and application metadata from
the request, then checks the actual saved three-channel graphs, Global schema/
owner registration and public saved-scene output. It checks oriented triangles
after metres-to-feet float32 conversion, metadata equality, identities, bounds,
references and render material resolution. The ordinary IFC exporter is not an
oracle for DirectShape because the pinned exporter does not map that class.

`seed-model-experiment.json` records source/candidate/request hashes and hashes
of complete local reports. Baseline complete evidence is in
`local/seed-model-verified-baseline`; large evidence is in
`local/seed-model-verified-large`. The12MB large native report remains local;
the durable summary includes its hash and deterministic fixture construction.
The first linear large fixture exceeded the explicit±10,000m coordinate limit
and was rejected before output creation. A110×100 grid preserves all11,000
triangles without changing that limit.

## Reproduce

```sh
python3 research/rvt/seed_model_experiment.py \
 research/rvt/local/minimal_seed-Project.rvt \
 research/rvt/local/NEW-combined-model \
 research/rvt/results/seed-model-request.json \
 --reader /home/brandonin/.cache/movingatoms-rvt-rs \
 --target research/rvt/local/seed-model-verified-build \
 --acknowledge-hypotheses
```

The runner checks source, pinned reader checkout, request, profiles, research
code and transport executable before/after verification. It records failures and
never overwrites an existing output directory or published candidate. Standalone
runtime mode accepts hash-bound prebuilt probes, without requiring a Rust SDK
or reader source checkout. Three runner binding tests pass; source-wide tests
were run by the parent before the frozen pipeline.

These are verified research candidates. Native application acceptance,
regeneration behavior, complete save lifecycle and default DirectShape option
semantics remain untested. `production_native_export` remainsfalse in both run
reports. Successful independent decoding/rendering is not an Autodesk acceptance
claim.
