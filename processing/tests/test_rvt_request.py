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
    assert wall['properties']['source_element'] == source['elements'][0]
    assert wall['properties']['representation']['part_metadata'] == [{'name': 'body', 'material': 'wall'}, {'name': 'second', 'material': 'wall'}]
    for i, part in enumerate(supplied['wall-1']):
        assert wall['parts'][i]['vertices'] == part.vertices.tolist()
        assert wall['parts'][i]['triangles'] == part.faces.tolist()
    assert source == before
    wall['properties']['source_element']['props']['nested']['a'].append('changed')
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
    assert explicit['elements'][0]['properties']['source_element']['kind'] == 'equipment'
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


def test_complete_source_context_and_element_metadata_preserved_exactly():
    source = read()
    source.update(project_id='project', seq=42, future_model={'x': [None, True]})
    source['levels'][0]['props']['future_level_property'] = {'rating': 9}
    source['types'] = [{'id': 'wall-type', 'params': {'material': 'stone'}, 'props': {'custom': [1, 2]}},
                       {'id': 'old-type', 'deleted': True, 'future': 'retained'}]
    element = source['elements'][0]
    element.update(params={'start': [0, 0], 'end': [2, 3], 'thickness': 0.2},
                   geometry={'mesh': {'sha': 'abc'}, 't': [1, 2, 3], 'q': [0, 0, 0, 1]},
                   type_id='wall-type', parent_id=None, future_element={'nullable': None})
    before = copy.deepcopy(source)
    request = to_seed_model_request(source, {'wall-1': [triangle()]})
    metadata = request['elements'][0]['properties']
    assert metadata['source_element'] == element
    assert metadata['source_context'] == {
        'levels': source['levels'], 'types': source['types'],
        'model_metadata': {'project_id': 'project', 'seq': 42, 'future_model': {'x': [None, True]}},
    }
    assert 'provenance' not in metadata['source_element']
    assert metadata['source_element']['parent_id'] is None
    metadata['source_context']['types'][0]['params']['material'] = 'mutated'
    metadata['source_context']['levels'][0]['props']['future_level_property']['rating'] = 0
    metadata['source_element']['geometry']['t'][0] = 99
    assert source == before


def test_model_input_records_only_available_live_context():
    source = read()
    source.update(project_id='unavailable-after-normalization', seq=8,
                  types=[{'id': 'live-type'}, {'id': 'deleted-type', 'deleted': True}])
    result = to_seed_model_request(Model(source), {'wall-1': [triangle()]})
    context = result['elements'][0]['properties']['source_context']
    assert context == {'levels': source['levels'], 'types': [{'id': 'live-type'}], 'model_metadata': {'seq': 8}}


@pytest.mark.parametrize('corruption', ['oversized', 'cycle', 'non_json', 'duplicate_type'])
def test_complete_metadata_is_bounded_without_silent_loss(corruption):
    source = read()
    if corruption == 'oversized':
        source['extra'] = 'x' * 500_001
    elif corruption == 'cycle':
        source['extra'] = source
    elif corruption == 'non_json':
        source['levels'][0]['props']['bad'] = {1, 2}
    else:
        source['types'] = [{'id': 'same'}, {'id': 'same'}]
    with pytest.raises(ValueError):
        to_seed_model_request(source, {'wall-1': [triangle()]})
