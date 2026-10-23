"""Guarded Level1916 graph encoder for the pinned empty 2024 seed.

Creates record bodies only. Elevation uses two horizontal Plane origins; this
is a measured geometry hypothesis, not validation of native regeneration.
"""
from copy import deepcopy
import math
from wall_element import GraphEncoder

SOURCE_SHA = '674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'


def encode_level(profile, element_id, name, elevation_feet, *, acknowledge_lifecycle_hypothesis=False):
    if profile['source_sha256'] != SOURCE_SHA:
        raise ValueError('pinned empty seed required')
    if not acknowledge_lifecycle_hypothesis:
        raise ValueError('level registration/view lifecycle remains unverified')
    if type(element_id) is not int or not 0 < element_id < 2**31:
        raise ValueError('positive measured int32 identity required')
    if not isinstance(name,str) or not name.strip() or '\0' in name:
        raise ValueError('nonempty level name required')
    if type(elevation_feet) not in (int,float) or not math.isfinite(elevation_feet):
        raise ValueError('finite elevation required')
    graphs=deepcopy(profile['graphs'])
    parents=[o for o in graphs['101']['objects'] if o['class_name']=='ElementParents']
    roots=[o for o in graphs['102']['objects'] if o['class_name']=='Level']
    planes=[o for o in graphs['102']['objects'] if o['class_name']=='Plane']
    if len(parents)!=1 or len(roots)!=1 or len(planes)!=2:
        raise ValueError('unexpected level graph profile')
    root=roots[0]['fields']
    if root['m_id']['m_id']['m_id64']!=1916 or root['m_attrId']['m_id']['m_id64']!=1910:
        raise ValueError('source identity/type differs')
    if [v['m_id']['m_id64'] for v in parents[0]['fields']['m_deletion']] != [1910,1916]:
        raise ValueError('source dependency profile differs')
    for k in ('m_ownerDBViewId','m_genDbViewId','m_assocLevelId'):
        if root[k]['m_id']['m_id64']!=-1:raise ValueError('unexpected view association')
    root['m_id']['m_id']['m_id64']=element_id
    root['m_text']=name
    parents[0]['fields']['m_deletion'][1]['m_id']['m_id64']=element_id
    for plane in planes:
        f=plane['fields']
        if f['m_origin'] != [0,0,0] or f['m_xVec'] != [1,0,0] or f['m_yVec'] != [0,1,0]:
            raise ValueError('expected horizontal origin level planes')
        f['m_origin'][2]=float(elevation_feet)
    # Datum annotation endpoints/reference points are zero/uninitialised in this
    # seed. Preserve them; translating them would invent a view-cache policy.
    encoder=GraphEncoder(profile['declarations'])
    return {int(c):encoder.graph(g) for c,g in graphs.items()}
