# Seed-specific wall context and schema mapping

The pinned minimal seed and Core Interior have **byte-identical inflated
Formats/Latest streams** (SHA-256
`0bfb947b3c9a0cec2ea9692873e3b0325f1c9387caaffddbce4cc2509e77cf21`).
A separate declaration comparison verifies every one of the wall encoder's
97 required classes: names, numeric tags, inheritance, versions, field
modifiers/counts/references, nested descriptors, flags and opaque entry hashes.
No schema-tag translation is required for this exact pair.

The independent context inventory decodes 1,494 current channel-102 records
across the seed's styles, materials, levels, wall types and phases. All decode
completely with zero off-route records. Source/seed file hashes and individual
context-record hashes are preserved in `seed_wall_context.json`.

| Core reference | Seed reference | Basis |
|---:|---:|---|
| 3 | 4 | New Construction phase |
| 87 | 91 | Entire Material field object is identical: Default Wall |
| 113 | 119 | Graphics style kind 1, category -2000011 |
| 119 | 125 | Graphics style kind 1, category -2000540 |
| 681 | 796 | Graphics style kind 1, category -2000896 |
| 17328 | 1947 | Seed BasicWallType; requires matching its 200 mm thickness |
| 20308 | 1916 | Base level, relocated from source elevation 76 ft to seed elevation 0 ft |
| 20307 | newly allocated upper level | Seed has only one Level; never collapse both constraints onto it |

Seed type 1947's body is 700 bytes, SHA-256
`c84b7cc77bcc4b5c06c14d78d2c522cbfc46f6fe39e0f189a3064ede55777c85`.
Its `CompoundStructure.m_layers[0].m_layerWidth` is
`0.6561679790026247` feet (200 mm), and its layer material is the inherited -1
sentinel. Wall category style 119 resolves to material 91, matching the remapped
face material. The source wall is 2/3 ft thick, so changing only the type ID
would be inconsistent. The separate `wall_thickness` encoder adapts geometry;
this remapper independently measures the encoded solid width before accepting it.

## Executable API

```python
from seed_wall_context import EXISTING_MAPPING, remap_graphs

mapped, audit = remap_graphs(
    generated_graphs, profile['declarations'],
    EXISTING_MAPPING | {20307: allocated_top_level},
    new_id=allocated_wall_id,
    base_elevation_feet=0.0,
    top_elevation_feet=15.0,
    type_width_feet=seed_context['seed_wall_type']['width_feet'],
)
```

Use this after the Core-profile height/length/yaw/thickness encoder and before
`GraphEncoder.graph`. The helper:

- Requires all eight external references and the seven measured seed mappings.
- Changes only schema-declared ElementId values, in one pass. This prevents the
  overlapping 113→119 and 119→125 mappings from cascading.
- Rejects unknown positive element references, missing mappings, a shared
  base/top level, or inconsistent owner identity.
- Measures solid width perpendicular to the horizontal driver line and rejects
  a mismatch with the supplied measured destination type width.
- Relocates the 14 plane origins, one line origin, header outline and two root
  bounds in Z. Local UVs, direction vectors, empty-cache boxes and graph pointers
  remain unchanged.
- Recomputes top-offset parameter -1001109 as wall height minus the destination
  top/base level separation. The cached height must already match the geometry;
  the base offset must be zero.
- Rechecks geometric edge consistency.

The document-access pointer token 1 and local geometry graph pointers are not
project ElementIds. They retain their observed roles; they are not blindly
rewritten as IDs.

## Independent construction check

A 200 mm-thick wall with length 12 ft, height 12 ft and yaw 37° is remapped to
base level 1916, planned top level 2746 and wall ID 2747. Its base moves by -76 ft,
and its top offset becomes -3 ft relative to the planned 15 ft upper level.
The helper changes 33 typed references and 18 world-coordinate fields.

All three encoded bodies decode through the **actual seed's embedded schema**
into exactly the generated graphs:

| Channel | Bytes | Objects | Edges |
|---:|---:|---:|---:|
| 101 | 233 | 3 | 2 |
| 102 | 2946 | 29 | 28 |
| 103 | 6884 | 74 | 73 |

The report binds each body hash. This check constructs record bodies only; it
does not insert the proposed upper level or wall into the seed. The save-builder
and level work provide those separate operations.

Four tests cover a yawed 200 mm wall, Z/constraint consistency, overlapping ID
mappings, type-width mismatch, collapsed levels, unexpected or missing IDs,
wrong existing seed mappings, and incompatible schemas.

```sh
python3 research/rvt/seed_wall_context.py \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  > research/rvt/results/seed_wall_context.json
python3 -m unittest discover -s research/rvt -p test_seed_wall_context.py
```

These checks do not establish signature acceptance, native cache regeneration,
or Autodesk application acceptance. They remove the source-wall's direct
foreign-project references and validate the measured record/schema conversion.
