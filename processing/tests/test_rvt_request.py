"""Pure offline model-to-research-request preservation and rejection checks."""
import copy
from pathlib import Path
import sys

import numpy as np
import pytest

from ma_proc.model.geometry import Model, Part
from ma_proc.model.rvt_request import to_seed_model_request


def triangle(name='body', x=0):
    return Part(name, 'wall', np.array([[x, 0., 1.], [x+1, 0., 1.], [x, 1., 1.]]), np.array([[0, 1, 2]]))


def read():
    return {'levels': [{'id': 'ground', 'kind': 'level', 'params': {'elevation': 1.25}, 'props': {'name': 'Ground'}}],
            'elements': [{'id': 'wall-1', 'kind': 'wall', 'level_id': 'ground', 'version': 3,
                          'props': {'name': 'Wall 😀', 'nested': {'a': [True, None, 4.2]}}}]}


def test_multipart_open_geometry_levels_and_properties_preserved():
    source = read()
    supplied = {'wall-1': [triangle(), triangle('second', 4)]}
    before = copy.deepcopy(source)
    request = to_seed_model_request(source, supplied)
    assert request['units'] == 'metres'
    assert request['levels'] == [{'id': 'ground', 'name': 'Ground', 'elevation': 1.25}]
    wall = request['elements'][0]
    assert wall['id'] == 'wall-1' and wall['name'] == 'Wall 😀' and wall['category'] == 'Wall'
    assert wall['level_id'] == 'ground'
    assert wall['properties']['props'] == source['elements'][0]['props']
    assert wall['properties']['part_metadata'] == [{'name': 'body', 'material': 'wall'}, {'name': 'second', 'material': 'wall'}]
    for i, part in enumerate(supplied['wall-1']):
        assert wall['parts'][i]['vertices'] == part.vertices.tolist()
        assert wall['parts'][i]['triangles'] == part.faces.tolist()
    assert source == before
    wall['properties']['props']['nested']['a'].append('changed')
    assert source == before
    # Integrate against the actual research contract without importing it into
    # production. This check detects request drift in the shared repository.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'research/rvt'))
    from seed_model_request import validate
    validate(to_seed_model_request(source, supplied))


@pytest.mark.parametrize('parts', [{}, {'wall-1': []}, {'wall-1': [triangle()], 'missing': [triangle()]}])
def test_live_geometry_is_never_silently_omitted(parts):
    with pytest.raises(ValueError):
        to_seed_model_request(read(), parts)


def test_deleted_source_is_excluded_but_stale_parts_rejected():
    source = read()
    source['elements'].append({'id': 'deleted', 'kind': 'generic', 'deleted': True})
    result = to_seed_model_request(source, {'wall-1': [triangle()]})
    assert [e['id'] for e in result['elements']] == ['wall-1']
    with pytest.raises(ValueError, match='extra'):
        to_seed_model_request(source, {'wall-1': [triangle()], 'deleted': [triangle()]})


def test_duplicate_source_and_parts_rejected():
    source = read()
    source['elements'].append(copy.deepcopy(source['elements'][0]))
    with pytest.raises(ValueError, match='duplicate source'):
        to_seed_model_request(source, {'wall-1': [triangle()]})
    for values in ([triangle(), triangle()], [triangle(), triangle('another')]):
        with pytest.raises(ValueError, match='duplicate part'):
            to_seed_model_request(read(), {'wall-1': values})


def test_unknown_category_requires_explicit_policy():
    source = read()
    source['elements'][0]['kind'] = 'equipment'
    with pytest.raises(ValueError, match='unsupported category'):
        to_seed_model_request(source, {'wall-1': [triangle()]})
    generic = to_seed_model_request(source, {'wall-1': [triangle()]}, allow_generic_fallback=True)
    assert generic['elements'][0]['category'] == 'GenericModel'
    explicit = to_seed_model_request(source, {'wall-1': [triangle()]}, category_overrides={'wall-1': 'MechanicalEquipment'})
    assert explicit['elements'][0]['category'] == 'MechanicalEquipment'
    assert explicit['elements'][0]['properties']['kind'] == 'equipment'
    with pytest.raises(ValueError):
        to_seed_model_request(source, {'wall-1': [triangle()]}, category_overrides={'wall-1': 'Imaginary'})


def test_openings_are_explicitly_unsupported_even_without_drawable_parts():
    source = read()
    source['elements'].append({'id': 'void', 'kind': 'opening', 'parent_id': 'wall-1'})
    with pytest.raises(ValueError, match='opening void.*baked void'):
        to_seed_model_request(source, {'wall-1': [triangle()]}, allow_generic_fallback=True)


def test_host_level_inheritance_and_missing_references():
    source = read()
    source['elements'].append({'id': 'door', 'kind': 'door', 'parent_id': 'wall-1', 'props': {'name': 'Door'}})
    parts = {'wall-1': [triangle()], 'door': [triangle()]}
    request = to_seed_model_request(Model(source), parts)
    assert request['elements'][1]['level_id'] == 'ground'
    source['elements'][1]['level_id'] = 'unknown'
    with pytest.raises(ValueError, match='level reference'):
        to_seed_model_request(source, parts)
    source['elements'][1].pop('level_id')
    source['elements'][1]['parent_id'] = 'unknown'
    with pytest.raises(ValueError, match='missing parent'):
        to_seed_model_request(source, parts)


@pytest.mark.parametrize('change', ['float_faces', 'nan', 'index', 'shape', 'props', 'level'])
def test_invalid_arrays_properties_and_levels_fail_closed(change):
    source = read()
    part = triangle()
    if change == 'float_faces':
        part.faces = part.faces.astype(float)
    elif change == 'nan':
        part.vertices[0, 0] = np.nan
    elif change == 'index':
        part.faces[0, 0] = 999
    elif change == 'shape':
        part.vertices = np.zeros((3, 2))
    elif change == 'props':
        source['elements'][0]['props']['bad'] = (1, 2)
    elif change == 'level':
        source['levels'][0]['params'].pop('elevation')
    with pytest.raises(ValueError):
        to_seed_model_request(source, {'wall-1': [part]})
