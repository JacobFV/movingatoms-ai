"""Change measured straight-wall length with coherent plane/edge UV geometry.

Applies an axis-aligned affine stretch in the wall's orthonormal frame. Plane
origins and applicable UV distances both change; directions remain unit vectors.
Only the audited planar rectangular source profile is supported.
"""
from copy import deepcopy
import itertools
import math
from wall_element import GraphEncoder,translated_wall


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def difference(a,b):return [x-y for x,y in zip(a,b)]
def norm(a):return math.sqrt(dot(a,a))


def validate_profile(profile):
    graphs=profile['graphs']
    if set(graphs)!={'101','102','103'}:raise ValueError('requires three measured channels')
    for seq,root,count in [('101','ElementHeader',3),('102','SWall',29),('103','GElement',74)]:
        if len(graphs[seq]['objects'])!=count or graphs[seq]['objects'][0]['class_name']!=root:
            raise ValueError('unmeasured wall graph shape')
    lines=[(seq,o) for seq,g in graphs.items() for o in g['objects'] if o['class_name']=='GLine']
    if len(lines)!=1 or lines[0][0]!='102':raise ValueError('additional or non-wall driver lines unsupported')
    empty=[[1e30,1e30,1e30],[-1e30,-1e30,-1e30]]
    caches=[o['fields'] for o in graphs['102']['objects'] if o['class_name']=='GElement']
    if len(caches)!=2 or any(c['m_bBox']!=empty or c['m_tightbBox']!=empty or c['m_subNodes'] or c['m_elementId']!=-1 for c in caches):
        raise ValueError('nonempty channel102 geometry caches unsupported')


def source_frame(profile):
    lines=[o for o in profile['graphs']['102']['objects'] if o['class_name']=='GLine']
    if len(lines)!=1:raise ValueError('requires one straight wall driver line')
    line=lines[0]['fields'];axis=line['m_dirVec'];params=line['m_endParams'];origin=line['m_origin']
    def finite(values,n):return len(values)==n and all(type(v)in (int,float) and math.isfinite(v) for v in values)
    if not finite(axis,3) or not finite(origin,3) or not finite(params,2):raise ValueError('finite origin/axis/end parameters required')
    t0,t1=params
    if not ((abs(abs(axis[0])-1)<1e-12 and abs(axis[1])<1e-12) or (abs(abs(axis[1])-1)<1e-12 and abs(axis[0])<1e-12)):
        raise ValueError('only measured world-axis-aligned wall bounds supported')
    if len(axis)!=3 or not math.isclose(norm(axis),1,abs_tol=1e-12) or abs(axis[2])>1e-12 or not t1>t0:
        raise ValueError('requires horizontal unit wall axis with positive length')
    anchor=[v+t0*d for v,d in zip(line['m_origin'],axis)]
    return anchor,axis,t1-t0


def plane_scale(plane,axis,scale):
    factors=[]
    for name in ('m_xVec','m_yVec'):
        direction=plane[name]
        if len(direction)!=3 or not math.isclose(norm(direction),1,abs_tol=1e-12):raise ValueError('plane basis not unit')
        cosine=dot(direction,axis)
        if abs(cosine)<1e-10:factors.append(1.0)
        elif math.isclose(abs(cosine),1,abs_tol=1e-10):factors.append(scale)
        else:raise ValueError('oblique plane basis unsupported')
    if abs(dot(plane['m_xVec'],plane['m_yVec']))>1e-10:raise ValueError('plane frame not orthogonal')
    return factors


def graph_links(graph):
    tokens={}
    for index,obj in enumerate(graph['objects']):
        token=obj['token']
        if token not in (0,0xffffffff):
            if token in tokens:raise ValueError('duplicate shared graph token')
            tokens[token]=index
    edges={e['pointer_offset']:e['target_object_index'] for e in graph['edges']}
    def target(pointer):
        if pointer['pointer_token']==0:return None
        if pointer['class_tag'] is not None:
            if pointer['offset']not in edges:raise ValueError('owning pointer not resolved')
            return edges[pointer['offset']]
        token=pointer['pointer_token']
        if token not in tokens:raise ValueError('external geometric pointer not local')
        return tokens[token]
    return target


def face_planes(graph):
    target=graph_links(graph);faces={}
    for index,obj in enumerate(graph['objects']):
        if obj['class_name']!='Face':continue
        plane_index=target(obj['fields']['m_pSurf'])
        if plane_index is None or graph['objects'][plane_index]['class_name']!='Plane':raise ValueError('requires planar wall faces')
        faces[index]=plane_index
    return target,faces


def edge_consistency(graph):
    target,faces=face_planes(graph);checked=0;max_error=0.0
    for obj in graph['objects']:
        if obj['class_name']!='Edge':continue
        fields=obj['fields']
        if fields['m_interiorEdgePnts']:raise ValueError('curved/interior edge points unsupported')
        face_indices=[target(p) for p in fields['m_pFace']]
        if face_indices[0] is None:raise ValueError('edge has no first face')
        for point in fields['m_firstAndLastEdgePnts']:
            world=[]
            for i,face in enumerate(face_indices):
                if face is None:continue
                plane=graph['objects'][faces[face]]['fields'];u,v=point['uv'][i]
                point_world=[plane['m_origin'][j]+u*plane['m_xVec'][j]+v*plane['m_yVec'][j] for j in range(3)]
                if any(not math.isfinite(v) for v in point_world):raise ValueError('nonfinite edge endpoint')
                world.append(point_world)
            if len(world)==2:
                error=norm(difference(world[0],world[1]));max_error=max(max_error,error);checked+=1
                if not math.isfinite(error) or error>1e-8:raise ValueError('adjacent face UVs produce inconsistent edge endpoint')
    if checked!=24:raise ValueError('expected twenty-four paired-face endpoints')
    return {'paired_face_endpoints_checked':checked,'maximum_endpoint_disagreement_feet':max_error}


def stretch_profile(profile,length_feet):
    if type(length_feet)not in (int,float) or not math.isfinite(length_feet) or not 0.01<=length_feet<=10000:
        raise ValueError('supported finite wall length is 0.01..10000 feet')
    validate_profile(profile)
    anchor,axis,old_length=source_frame(profile)
    # Preserve the exact source stream at its nominal measured 9.5ft length.
    scale=1.0 if math.isclose(length_feet,old_length,rel_tol=0,abs_tol=1e-12) else length_feet/old_length
    result=deepcopy(profile);changes=[]
    def world(point):
        if len(point)!=3 or any(not math.isfinite(v) for v in point):raise ValueError('invalid XYZ point')
        if scale==1:return point[:]
        distance=dot(difference(point,anchor),axis)
        return [point[i]+(scale-1)*distance*axis[i] for i in range(3)]
    def uv(point,factors):
        if len(point)!=2:raise ValueError('UV point width')
        return [point[i]*factors[i] if factors[i]!=1 else point[i] for i in range(2)]
    def replace_field(seq,index,fields,key,value):
        if fields[key]!=value:changes.append({'channel':int(seq),'object':index,'field':key,'before':deepcopy(fields[key]),'after':deepcopy(value)})
        fields[key]=value
    for seq,graph in result['graphs'].items():
        target,faces=face_planes(graph)
        scales={i:plane_scale(graph['objects'][i]['fields'],axis,scale) for i in set(faces.values())}
        for index,obj in enumerate(graph['objects']):
            fields=obj['fields'];name=obj['class_name']
            if name in ('Plane','GLine'):
                replace_field(seq,index,fields,'m_origin',world(fields['m_origin']))
            if name=='GLine':
                replace_field(seq,index,fields,'m_endParams',[v*scale if scale!=1 else v for v in fields['m_endParams']])
            if name=='Plane':
                factors=plane_scale(fields,axis,scale)
                envelope=deepcopy(fields['m_Envelope']);envelope['m_corners']=[uv(p,factors) for p in envelope['m_corners']]
                replace_field(seq,index,fields,'m_Envelope',envelope)
            bounds=[]
            if seq=='101' and name=='Outline':bounds=['m_minmax']
            if seq=='103' and index==0:bounds=['m_bBox','m_tightbBox']
            for key in bounds:
                old=fields[key]
                if scale==1:value=deepcopy(old)
                else:
                    corners=[world(list(c)) for c in itertools.product(*zip(old[0],old[1]))]
                    value=[[min(p[i] for p in corners) for i in range(3)],[max(p[i] for p in corners) for i in range(3)]]
                replace_field(seq,index,fields,key,value)
            if name=='Edge':
                if fields['m_interiorEdgePnts']:raise ValueError('unsupported interior edge points')
                value=deepcopy(fields['m_firstAndLastEdgePnts'])
                for side,pointer in enumerate(fields['m_pFace']):
                    face=target(pointer)
                    if face is not None:
                        factors=scales[faces[face]]
                        for point in value:point['uv'][side]=uv(point['uv'][side],factors)
                replace_field(seq,index,fields,'m_firstAndLastEdgePnts',value)
            if name=='EdgeLoop':
                face=target(fields['m_pFace'])
                if face is None:raise ValueError('unowned edge loop')
                value=deepcopy(fields['m_Envelope']);value['m_corners']=[uv(p,scales[faces[face]]) for p in value['m_corners']]
                replace_field(seq,index,fields,'m_Envelope',value)
            if name=='GFilling':
                if fields['m_patternId']['m_id']['m_id64']!=-1:raise ValueError('patterned face placement unsupported')
                face=target(fields['m_pGFace'])
                if face is None:raise ValueError('unowned filling')
                value=deepcopy(fields['m_placer']);value['m_origin']=uv(value['m_origin'],scales[faces[face]])
                replace_field(seq,index,fields,'m_placer',value)
    source_check=edge_consistency(profile['graphs']['103'])
    changed_check=edge_consistency(result['graphs']['103'])
    return result,{'source_length_feet':old_length,'requested_length_feet':length_feet,'scale':scale,
                   'fixed_axis_start_feet':anchor,'axis_unit_vector':axis,'changes':changes,
                   'source_edge_consistency':source_check,'changed_edge_consistency':changed_check}


def encode_wall(profile,new_id,*,length_feet,translation_xy,context,room_bounding=None,acknowledge_bounding_hypothesis=False):
    changed,audit=stretch_profile(profile,length_feet)
    bodies,graphs,moves,identities=translated_wall(changed,new_id,translation_xy,context,
        room_bounding=room_bounding,acknowledge_bounding_hypothesis=acknowledge_bounding_hypothesis)
    audit['translation_moves']=moves;audit['self_identity_changes']=identities
    audit['final_edge_consistency']=edge_consistency(graphs['103'])
    return bodies,graphs,audit
