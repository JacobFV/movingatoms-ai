# Empty-seed level encoding audit

The MIT-licensed 2024 `Project.rvt` seed (SHA-256
`674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe`)
contains one Level, ID 1916, named `Level 1`. Its current channels reconstruct
byte for byte from the embedded schema: 135, 740 and 2 bytes, respectively.
They contain 2, 8 and 1 objects. The context type is LevelAttributes 1910.
`seed_level-profile.json` retains the complete graphs and transitive schema;
`seed_level-audit.json` records checksums and independent decoder results.

`seed_level.encode_level` emits all three record bodies for a positive ID,
Unicode name and finite elevation in native feet. It changes two self-ID
fields, `Level.m_text` and the Z coordinate of both horizontal Plane origins.
Four independently decoded variants cover zero, positive and negative heights,
variable-length text, Greek text and a non-BMP emoji. Original-profile input
reproduces the source exactly. The encoder requires explicit acknowledgment
that native creation lifecycle remains unverified. It does not allocate IDs,
modify a file, register levels or claim application acceptance.

The two Plane elevations are not an arbitrary numerical guess. Independently
extracted current Core 2024 levels 20307,20308 and 65128 have both Plane origins
at 91,76 and 185.5 feet respectively. Their bubble/free endpoints and new-view
reference points are all zero. The seed encoder preserves those zero annotation
values, directions, UV envelopes and empty graphics. The pinned public reader's
generic typed Level decoder expects `m_name`/`m_elevation`, unlike this file's
actual `m_text`/Plane representation; validation uses the complete schema graph
instead of treating missing typed projection fields as proof.

## Registration and view dependencies

The seed's complete Global graph references 1916 in:

- `ElementTrackingData`, category -2000240 (levels).
- `DatumTracking`'s datum ID set.
- `LevelPlanViewTracking`, mapping 1916 to existing plan 1936.
- Four MEP level-to-offset default maps in `AbsLayoutAppInfo`.
- Three parameter-value sets whose default base level is 1916.

Adding a level should extend the level category and datum lists under the measured registration hypothesis. Existing plan,
MEP defaults and base-level settings belong to the retained seed level; copying
or replacing them would change unrelated state. Whether a new level with no
plan view needs an empty map entry remains uncertain: Core 2024 contains 74
current Level graphs but only 15 LevelPlanViewTracking entries, including an
empty entry for 65128. Thus empty entries exist, but presence is not universal.
The explicit seed registration implementation and its policy are owned by the
separate save-context experiment.

The independent incoming scan decodes all 6900 current seed channel records
with zero unsupported graphs or off-route records. External references to 1916
belong to SketchPlanes 1926/1945, DBViewPlan 1936, SunAndShadowSettings 1939,
header 1944 and EnergyDataSettings 2017. These existing references are retained;
they are not additional records to clone for a new upper level. No native
regeneration or created-view behavior has been established.

## Reproduction

From the repository root, with pinned seed and Core 2024 fixtures present:

```sh
uv run --with olefile python research/rvt/seed_level_audit.py \
  --reader /home/brandonin/.cache/movingatoms-rvt-rs
python3 -m unittest discover -s research/rvt -p test_seed_level.py
```

The audit builds the pinned public Rust reader probe, verifies clean reader
source and fixture hashes, reconstructs the source bodies, independently
decodes generated bodies, scans incoming references, and re-decodes both
Global graphs. Four focused tests cover reconstruction, parameter variants,
measured nonzero-level controls and rejection of invalid inputs.
