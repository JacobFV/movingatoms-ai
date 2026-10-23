"""Pure adapter to the experimental SI-mesh request; never enables RVT export.

Parts must already be world-space metres, as produced by model.geometry. Native
category/lifecycle support is still subject to the research builder's checks.
Openings are rejected because supplied meshes alone cannot prove a baked void.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

import numpy as np

from .geometry import IFC_CLASS, Model, Part, ifc_class_of

KIND_CATEGORIES = {
    'wall': 'Wall', 'slab': 'Floor', 'door': 'Door', 'window': 'Window',
    'column': 'Column', 'beam': 'StructuralFraming', 'pipe': 'Pipe', 'duct': 'Duct',
    'pipe_fitting': 'PipeFitting', 'duct_fitting': 'DuctFitting', 'stair': 'Stair',
    'railing': 'Railing', 'roof': 'Roof', 'furniture': 'Furniture', 'generic': 'GenericModel',
}
# Canonical labels present in the measured minimal-seed category profile. This
# allowlist does not claim that Autodesk accepts every category on DirectShape.
CATEGORIES = frozenset(KIND_CATEGORIES.values()) | {
    'ArcWall', 'BuildingPad', 'Ceiling', 'StairsRun', 'StairsLanding', 'StairsStringer',
    'Ramp', 'StructuralColumn', 'StructuralFoundation', 'CurtainWallMullion',
    'CurtainWallPanel', 'WallSweep', 'Room', 'Casework', 'LightingFixture',
    'ElectricalEquipment', 'ElectricalFixture', 'MechanicalEquipment', 'LightingDevice',
    'FireAlarmDevice', 'DataDevice', 'PlumbingFixture', 'SpecialtyEquipment', 'Mass',
    'DuctTerminal', 'FoodServiceEquipment', 'Planting', 'Parking', 'Entourage',
    'Hardscape', 'VerticalCirculation', 'SlabEdge',
}


def _label(value, field):
    if not isinstance(value, str) or not value or value != value.strip() or '\0' in value or len(value) > 128:
        raise ValueError(f'{field} must be a trimmed nonempty string of at most 128 characters')
    try:
        value.encode('utf-16-le')
    except UnicodeEncodeError as error:
        raise ValueError(f'{field} contains invalid Unicode') from error
    return value


def _number(value, limit, field):
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
        raise ValueError(f'{field} must be finite within +/-{limit}')
    return float(value)


def _json_copy(value):
    def check(item):
        if item is None or type(item) in (bool, int):
            return
        if type(item) is float:
            _number(item, 1e300, 'property number')
        elif isinstance(item, str):
            if '\0' in item:
                raise ValueError('NUL in property')
            item.encode('utf-16-le')
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError('property keys must be strings')
                check(key)
                check(child)
        else:
            raise ValueError('properties must contain finite JSON types')
    try:
        check(value)
        if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-16-le')) > 1_000_000:
            raise ValueError('property payload exceeds 1MB')
    except (UnicodeEncodeError, RecursionError) as error:
        raise ValueError('invalid Unicode or excessive property nesting') from error
    return deepcopy(value)


def to_seed_model_request(model: Model | dict, parts: dict[str, list[Part]], *,
                          category_overrides: dict[str, str] | None = None,
                          allow_generic_fallback: bool = False) -> dict:
    """Preserve every supplied live product and part, or raise before export.

    Pass raw model-read data to also detect duplicate IDs before Model's existing
    dictionary normalization and preserve full original levels/types/model metadata.
    A Model instance retains only live level/type records and seq; it cannot recover
    deleted records, overwritten IDs, or omitted top-level source metadata. Deleted elements are excluded; supplying
    parts for them is an error. Unknown kinds need an explicit category override
    or explicit generic fallback. No level is assigned by proximity/default.
    """
    if type(allow_generic_fallback) is not bool:
        raise ValueError('generic fallback must be an explicit boolean')
    if isinstance(model, dict):
        source_context = {
            'levels': model.get('levels', []),
            'types': model.get('types', []),
            'model_metadata': {k: v for k, v in model.items() if k not in ('elements', 'levels', 'types')},
        }
        if not isinstance(source_context['types'], list):
            raise ValueError('types must be a list')
        seen_types = set()
        for source_type in source_context['types']:
            if not isinstance(source_type, dict):
                raise ValueError('type record must be an object')
            type_id = _label(source_type.get('id'), 'type ID')
            if type_id in seen_types:
                raise ValueError(f'duplicate source type ID: {type_id}')
            seen_types.add(type_id)
        seen = set()
        for collection in ('levels', 'elements'):
            rows = model.get(collection, [])
            if not isinstance(rows, list):
                raise ValueError(f'{collection} must be a list')
            for element in rows:
                if not isinstance(element, dict):
                    raise ValueError('element must be an object')
                ident = _label(element.get('id'), 'element ID')
                if ident in seen:
                    raise ValueError(f'duplicate source element ID: {ident}')
                seen.add(ident)
                if collection == 'levels' and element.get('kind') != 'level':
                    raise ValueError('levels collection contains nonlevel')
        model = Model(model)
    elif isinstance(model, Model):
        source_context = {'levels': model.levels, 'types': list(model.types.values()),
                          'model_metadata': {'seq': model.seq}}
    if not isinstance(model, Model) or not isinstance(parts, dict):
        raise ValueError('Model/read object and explicit parts dictionary required')
    overrides = {} if category_overrides is None else category_overrides
    if not isinstance(overrides, dict):
        raise ValueError('category overrides must be an element-ID dictionary')
    live = model.elements
    products = {i: e for i, e in live.items() if e.get('kind') != 'level'}
    if not 1 <= len(products) <= 100:
        raise ValueError('requires 1..100 live nonlevel products')
    for ident, element in products.items():
        if element.get('kind') == 'opening' or element.get('ifc_class') == 'IfcOpeningElement':
            raise ValueError(f'opening {ident}: baked void semantics cannot be proven from supplied parts')
    if set(parts) != set(products):
        raise ValueError(f'geometry inventory differs: missing={sorted(set(products)-set(parts))}, extra={sorted(set(parts)-set(products))}')
    if set(overrides) - set(products):
        raise ValueError('category override refers to a missing/deleted/level element')
    levels = []
    names = set()
    for element in model.levels:
        ident = _label(element.get('id'), 'level ID')
        props = element.get('props', {})
        params = element.get('params', {})
        if not isinstance(props, dict) or not isinstance(params, dict):
            raise ValueError('level properties and params must be objects')
        name = _label(props.get('name', ident), 'level name')
        elevation = _number(params.get('elevation'), 1000, 'level elevation')
        if name.casefold() in names:
            raise ValueError('duplicate level name')
        names.add(name.casefold())
        if name.casefold() == 'level 1' and (name != 'Level 1' or elevation != 0):
            raise ValueError('reserved seed Level 1 requires exact name and elevation 0')
        levels.append({'id': ident, 'name': name, 'elevation': elevation})
    level_ids = {x['id'] for x in levels}
    if len(levels) > 100 or len(products) + sum(x['name'] != 'Level 1' for x in levels) > 100:
        raise ValueError('native document allocation budget exceeded')
    elements = []
    vertex_count = triangle_count = 0
    for ident, element in products.items():
        if _label(ident, 'element ID') != element.get('id') or element.get('deleted'):
            raise ValueError('invalid live Model identity')
        kind = _label(element.get('kind'), 'element kind')
        if kind == 'opening' or element.get('ifc_class') == 'IfcOpeningElement':
            raise ValueError(f'opening {ident}: baked void semantics cannot be proven from supplied parts')
        category = overrides.get(ident)
        if category is None:
            category = KIND_CATEGORIES.get(kind)
            if element.get('ifc_class') not in (None, IFC_CLASS.get(kind)):
                category = None
            if category is None:
                if not allow_generic_fallback:
                    raise ValueError(f'unsupported category for {ident} ({kind}); explicit mapping required')
                category = 'GenericModel'
        if category not in CATEGORIES:
            raise ValueError(f'unsupported explicit native category: {category}')
        props = element.get('props', {})
        if not isinstance(props, dict):
            raise ValueError('element properties must be an object')
        name = _label(props.get('name', ident), 'element name')
        host_id = element.get('parent_id')
        if host_id is not None:
            _label(host_id, 'parent ID')
        if element.get('level_id') is not None:
            _label(element['level_id'], 'level ID')
        host = model.get(host_id)
        if host_id is not None and host is None:
            raise ValueError(f'missing parent for {ident}')
        level_id = element.get('level_id') or (host or {}).get('level_id')
        if level_id is not None and level_id not in level_ids:
            raise ValueError(f'missing/nonlevel level reference for {ident}')
        supplied = parts[ident]
        if not isinstance(supplied, list) or not 1 <= len(supplied) <= 100:
            raise ValueError(f'{ident} requires 1..100 explicit nonempty parts')
        encoded = []
        part_metadata = []
        part_names = set()
        geometries = set()
        for part in supplied:
            if not isinstance(part, Part):
                raise ValueError('parts must be geometry.Part instances')
            part_name = _label(part.name, 'part name')
            _label(part.material, 'part material')
            if part_name in part_names:
                raise ValueError(f'duplicate part name in {ident}')
            part_names.add(part_name)
            vertices = np.asarray(part.vertices)
            faces = np.asarray(part.faces)
            if vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices) or vertices.dtype.kind not in 'fiu':
                raise ValueError('vertices require a nonempty numeric Nx3 array')
            if faces.ndim != 2 or faces.shape[1] != 3 or not len(faces) or faces.dtype.kind not in 'iu':
                raise ValueError('faces require a nonempty integer Nx3 array')
            if not np.isfinite(vertices).all() or np.abs(vertices).max() > 10000:
                raise ValueError('world-metre vertices must be finite within +/-10000')
            if (faces < 0).any() or (faces >= len(vertices)).any():
                raise ValueError('face index outside part')
            vertex_count += len(vertices)
            triangle_count += len(faces)
            if vertex_count > 100000 or triangle_count > 200000:
                raise ValueError('document mesh budget exceeded')
            points = vertices.astype(np.float64)
            indices = faces.astype(np.int64)
            key = (points.tobytes(), indices.tobytes())
            if key in geometries:
                raise ValueError(f'duplicate part geometry in {ident}')
            geometries.add(key)
            encoded.append({'vertices': points.tolist(), 'triangles': indices.tolist()})
            part_metadata.append({'name': part_name, 'material': part.material})
        properties = _json_copy({'source_element': element,
                                'representation': {'ifc_class': ifc_class_of(element), 'part_metadata': part_metadata},
                                'source_context': source_context})
        result = {'id': ident, 'name': name, 'category': category, 'properties': properties, 'parts': encoded}
        if level_id is not None:
            result['level_id'] = level_id
        elements.append(result)
    return {'schema_version': 1, 'units': 'metres', 'levels': levels, 'elements': elements}
