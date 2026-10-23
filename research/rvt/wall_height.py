"""Bounded vertical wall change retaining measured base/top level constraints."""
from copy import deepcopy
import itertools
import math
from wall_parametric import validate_profile, plane_scale, face_planes, edge_consistency
from wall_oriented import encode_wall as oriented_encode


def height_profile(profile,height_feet):
    if type(height_feet) not in (int,float) or not math.isfinite(height_feet) or not 0.01<=height_feet<=10000:
        raise ValueError('finite height within0.01..10000 feet required')
    validate_profile(profile)
    root=profile['graphs']['102']['objects'][0]['fields']
    if root['m_assocLevelId']['m_id']['m_id64']!=20308 or root['m_upToLevelId']['m_id']['m_id64']!=20307:
        raise ValueError('requires measured base20308/top20307 context')
    params=[o for o in profile['graphs']['102']['objects'] if o['class_name']=='ParamValueSetDouble']
    if len(params)!=1:raise ValueError('requires one scalar parameter set')
    values={v['m_paramId']['m_id']['m_id64']:v['m_value'] for v in params[0]['fields']['m_paramSet']}
    expected={-1012829:0.0,-1012828:0.0,-1001111:0.0,-1001109:0.0,-1001108:0.0,-1001105:8.0,-1001101:15.0}
    if values!=expected or len(params[0]['fields']['m_paramSet'])!=len(expected):
        raise ValueError('unmeasured height/offset parameter state')
    bbox=profile['graphs']['103']['objects'][0]['fields']['m_bBox']
    if bbox[0][2]!=76.0 or bbox[1][2]!=91.0:raise ValueError('source geometry does not match audited levels')
    axis=[0.0,0.0,1.0];anchor=[0.0,0.0,76.0];scale=height_feet/15.0
    result=deepcopy(profile);changes=[]
    def world(point):
        if len(point)!=3 or any(not math.isfinite(v) for v in point):raise ValueError('invalid XYZ point')
        if scale==1:return point[:]
        distance=point[2]-anchor[2]
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
    param_objects=[o for o in result['graphs']['102']['objects'] if o['class_name']=='ParamValueSetDouble']
    for item in param_objects[0]['fields']['m_paramSet']:
        ident=item['m_paramId']['m_id']['m_id64']
        if ident in (-1001109,-1001101):
            before=item['m_value'];after=height_feet-15.0 if ident==-1001109 else height_feet
            if before!=after: changes.append({'channel':102,'parameter_id':ident,'before':before,'after':after})
            item['m_value']=after
    return result,{'height_feet':height_feet,'base_elevation_feet':76.0,'top_level_elevation_feet':91.0,
        'top_offset_feet':height_feet-15.0,'cached_height_parameter_id':-1001101,
        'changes':changes,'edge_consistency':edge_consistency(result['graphs']['103'])}


def encode_wall(profile,new_id,*,height_feet=15.0,length_feet,translation_xy,context,yaw_degrees=0,room_bounding=None,acknowledge_bounding_hypothesis=False):
    changed,height_audit=height_profile(profile,height_feet)
    bodies,graphs,audit=oriented_encode(changed,new_id,length_feet=length_feet,translation_xy=translation_xy,context=context,
        yaw_degrees=yaw_degrees,room_bounding=room_bounding,acknowledge_bounding_hypothesis=acknowledge_bounding_hypothesis)
    if height_feet!=15.0:audit['height']=height_audit
    return bodies,graphs,audit
