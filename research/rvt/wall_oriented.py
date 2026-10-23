"""Rigid yaw of the measured planar wall, after its longitudinal stretch."""
from copy import deepcopy
import math
from wall_parametric import stretch_profile, source_frame, graph_links, edge_consistency
from wall_element import translated_wall


def checked_yaw(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not -360 <= value <= 360:
        raise ValueError('finite yaw within -360..360 degrees required')
    return float(value)


def solid_vertices(graph):
    """Extract actual six-face solid endpoints; exclude four open reference sheets."""
    resolve = graph_links(graph); objects = graph['objects']
    solids = [o for o in objects if o['class_name'] == 'Geometry' and len(o['fields']['m_pFaces']) == 6 and len(o['fields']['m_pEdges']) == 12]
    if len(solids) != 1:
        raise ValueError('requires one measured six-face twelve-edge solid')
    fields = solids[0]['fields']; faces = {resolve(p) for p in fields['m_pFaces']}; vertices = []
    if None in faces or len(faces) != 6: raise ValueError('invalid solid faces')
    for pointer in fields['m_pEdges']:
        edge = objects[resolve(pointer)]
        if edge['class_name'] != 'Edge': raise ValueError('solid edge class differs')
        ef = edge['fields']; sides = [resolve(p) for p in ef['m_pFace']]
        if len(sides) != 2 or len(set(sides)) != 2 or any(f not in faces for f in sides):
            raise ValueError('solid edge is not paired within solid')
        face = objects[sides[0]]
        if face['class_name'] != 'Face': raise ValueError('solid face class differs')
        plane = objects[resolve(face['fields']['m_pSurf'])]
        if plane['class_name'] != 'Plane': raise ValueError('nonplanar solid')
        pf = plane['fields']
        for endpoint in ef['m_firstAndLastEdgePnts']:
            u, v = endpoint['uv'][0]
            point = [pf['m_origin'][i]+u*pf['m_xVec'][i]+v*pf['m_yVec'][i] for i in range(3)]
            if any(not math.isfinite(x) for x in point): raise ValueError('nonfinite solid vertex')
            if not any(math.dist(point, old) < 1e-8 for old in vertices): vertices.append(point)
    if len(vertices) != 8: raise ValueError('requires eight distinct solid vertices')
    return vertices


def yaw_profile(profile, yaw_degrees):
    angle = checked_yaw(yaw_degrees)
    anchor, _, _ = source_frame(profile)
    # Zero preserves original encoded values, including measured tiny roundoff.
    if angle == 0:
        return deepcopy(profile), {'yaw_degrees': 0.0, 'anchor_feet': anchor, 'changes': []}
    result = deepcopy(profile); changes = []
    radians = math.radians(angle); cosine, sine = math.cos(radians), math.sin(radians)
    def vector(value):
        if len(value) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
            raise ValueError('finite world vector required')
        return [cosine*value[0]-sine*value[1], sine*value[0]+cosine*value[1], value[2]]
    def point(value): return [a+b for a,b in zip(anchor, vector([v-a for v,a in zip(value,anchor)]))]
    def replace(seq, index, fields, key, value):
        changes.append({'channel': int(seq), 'object': index, 'field': key, 'before': deepcopy(fields[key]), 'after': deepcopy(value)})
        fields[key] = value
    plane_count = line_count = 0
    for seq, graph in result['graphs'].items():
        for index, obj in enumerate(graph['objects']):
            name, fields = obj['class_name'], obj['fields']
            if name == 'Plane':
                plane_count += 1
                x,y = fields['m_xVec'],fields['m_yVec']
                if abs(math.dist(x,[0,0,0])-1)>1e-10 or abs(math.dist(y,[0,0,0])-1)>1e-10 or abs(sum(a*b for a,b in zip(x,y)))>1e-10:
                    raise ValueError('plane frame must be orthonormal')
                for key in ('m_xVec','m_yVec'): replace(seq,index,fields,key,vector(fields[key]))
            if name == 'GLine':
                line_count += 1
                replace(seq,index,fields,'m_dirVec',vector(fields['m_dirVec']))
            if name in ('Plane','GLine'): replace(seq,index,fields,'m_origin',point(fields['m_origin']))
    if (plane_count,line_count) != (14,1): raise ValueError('unmeasured world frame inventory')
    vertices = solid_vertices(result['graphs']['103'])
    bounds = [[min(p[i] for p in vertices) for i in range(3)], [max(p[i] for p in vertices) for i in range(3)]]
    outlines = [(i,o) for i,o in enumerate(result['graphs']['101']['objects']) if o['class_name']=='Outline']
    if len(outlines)!=1: raise ValueError('requires one header outline')
    index,obj=outlines[0]; replace('101',index,obj['fields'],'m_minmax',deepcopy(bounds))
    for key in ('m_bBox','m_tightbBox'): replace('103',0,result['graphs']['103']['objects'][0]['fields'],key,deepcopy(bounds))
    return result, {'yaw_degrees':angle,'anchor_feet':anchor,'changes':changes,'solid_vertices_before_translation':vertices,
                    'edge_consistency':edge_consistency(result['graphs']['103'])}


def encode_wall(profile,new_id,*,length_feet,translation_xy,context,yaw_degrees=0,room_bounding=None,acknowledge_bounding_hypothesis=False):
    checked_yaw(yaw_degrees)
    changed,audit=stretch_profile(profile,length_feet)
    changed,yaw_audit=yaw_profile(changed,yaw_degrees)
    bodies,graphs,moves,identities=translated_wall(changed,new_id,translation_xy,context,
        room_bounding=room_bounding,acknowledge_bounding_hypothesis=acknowledge_bounding_hypothesis)
    audit['translation_moves']=moves; audit['self_identity_changes']=identities
    audit['final_edge_consistency']=edge_consistency(graphs['103'])
    # Preserve legacy zero-yaw audit shape as well as its graph and body bytes.
    if yaw_degrees != 0: audit['yaw']=yaw_audit
    return bodies,graphs,audit
