# Measured category contexts for the minimal seed

The hash-pinned MIT Revit 2024 seed contains **1,457 graphics-style elements and
33 material elements**. The independent pinned reader decodes all 1,490 current
channel-102 records completely with zero off-route records. Each saved style,
category, style kind and material reference is recorded with its actual element
identity, source stream and body hash in `seed_categories.json`.

The helper joins actual seed styles to the pinned public reader's
[`partition_element_records.rs` category constants](https://github.com/DrunkOnJava/rvt-rs/blob/b6086d41b9758fd9b92f42f0a47b8345b9c58056/src/partition_element_records.rs)
and [`ifc/category_map.rs` class declarations](https://github.com/DrunkOnJava/rvt-rs/blob/b6086d41b9758fd9b92f42f0a47b8345b9c58056/src/ifc/category_map.rs).
Both public source files are hash-bound in the report. It advertises 47 measured
class/category contexts; public classes without an explicit supported join are
listed separately. Unknown categories are never invented.

| Requested kind | Saved category | Projection style | Cut style | Projection material |
|---|---:|---:|---:|---:|
| GenericModel | -2000151 | 413 | 414 | -1 |
| Wall | -2000011 | 119 | 120 | 91 |
| Floor / slab | -2000032 | 229 | 230 | -1 |
| Door | -2000023 | 217 | 218 | -1 |
| Window | -2000014 | 205 | 206 | -1 |
| Column | -2000100 | 303 | 304 | -1 |
| StructuralColumn | -2001330 | 571 | 572 | -1 |
| StructuralFraming / beam | -2001320 | 537 | 538 | -1 |
| Pipe | -2008044 | 996 | absent | -1 |
| Duct | -2008000 | 937 | absent | -1 |
| Roof | -2000035 | 237 | 238 | 92 |
| Stair | -2000120 | 307 | 308 | -1 |
| Furniture | -2000080 | 299 | 300 | -1 |

Material -1 is the saved **unassigned sentinel**. Material 91 is Default Wall;
material 92 is Default Roof. A positive material ID is returned only when the
inventory contains its actual MaterialElem record. Thirty-six other styles
reference negative built-in material values such as -4000010; those raw values
remain recorded, but the chooser refuses them because this audit does not
resolve them to material owners.

## Caller API

```python
from seed_categories import context_for

context = context_for('slab', interior_policy='projection')
# category_id=-2000032, style_id=229, interior_style_id=229, material_id=-1

cut = context_for('wall', interior_policy='cut')
# style_id=119, interior_style_id=120, material_id=91

fallback = context_for('unsupported kind', interior_policy='projection',
                       allow_generic_fallback=True)
# GenericModel category -2000151 / style 413; generic_fallback_used=True
```

`interior_policy` is a required keyword. Choices:

- `projection`: use the measured projection style for both root graphics and
  polymesh interior rendering.
- `cut`: retain the projection style at the root and use the measured same-category
  cut style for the interior. Missing cut styles, including Pipe/Duct, are rejected.
- `explicit`: require `explicit_interior_style_id` naming an actual measured seed
  GStyleElem. Its category is returned separately. For example, style 125 belongs
  to category -2000540; it is not generalized into a universal fill style.

Unknown kinds fail unless the caller explicitly sets the boolean
`allow_generic_fallback=True`. The result records requested/effective kind,
fallback usage, interior policy, selected style source evidence and the public
IFC mapping. Input strings are case-insensitive; documented aliases include
`slab`→Floor and `beam`→StructuralFraming. Numerical category input is not accepted.

Returned constructor fields are `category_id`, `style_id`, `interior_style_id`,
and `material_id`. The constructor must actually apply `material_id` to
`GPolyMesh.m_materialID` if it chooses this material policy; merely returning a
context dictionary does not change saved model bytes.

## What this establishes

The selected IDs exist in the exact seed and their fields decode as reported.
Choosing projection/cut/another measured interior style is an **explicit caller
hypothesis**. Public saved-scene rendering resolves `GPolyMesh.m_interiorGStyleID`,
so projection style 413 gives a defensible generic rendering context. That does
not prove Autodesk accepts DirectShape in every listed category, or establish
universal DirectShape defaults. Categorized DirectShape geometry is not a native
parametric wall, hosted door, or MEP system merely because its category matches.
The public IFC class mapping does not add DirectShape support to that exporter.

## Reproduce

```sh
python3 research/rvt/seed_categories.py \
  --reader-source /home/brandonin/.cache/movingatoms-rvt-rs \
  > research/rvt/results/seed_categories.json
python3 -m unittest discover -s research/rvt -p test_seed_categories.py
```

Six tests pass, covering principal categories/aliases, explicit fallback,
projection/cut/explicit policies, absent cut styles, unresolved materials,
provenance mismatches and every advertised context's positive-ID joins.
No model or public-reader source is modified.
