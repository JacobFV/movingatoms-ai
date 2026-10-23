"""Measured single-layer wall thickness geometry; changed widths require type remapping."""
from copy import deepcopy
import itertools
import math
from wall_parametric import validate_profile, source_frame, plane_scale, face_planes, edge_consistency, dot, difference
from wall_height import encode_wall as height_encode
from wall_oriented import solid_vertices
SOURCE_WIDTH=2/3


def thickness_profile(profile,width_feet):
    if type(width_feet)not in(int,float)or not math.isfinite(width_feet)or not 0.01<=width_feet<=10:
        raise ValueError('finite measured-family width within0.01..10 feet required')
    validate_profile(profile)
    fields=profile['graphs']['102']['objects'][0]['fields']
    if fields['m_wallKeyRef']!=2 or fields['m_isFlipped'] or fields['m_keyRefOffset']!=SOURCE_WIDTH/2 or fields['m_locLineOffset']!=0:
        raise ValueError('requires measured unflipped key-reference2 and half-width offset')
    anchor,longitudinal,_=source_frame(profile)
    axis=[-longitudinal[1],longitudinal[0],0.0];scale=width_feet/SOURCE_WIDTH
    normal_coordinates=[dot(difference(p,anchor),axis) for p in solid_vertices(profile['graphs']['103'])]
    if abs(min(normal_coordinates)+SOURCE_WIDTH/2)>1e-8 or abs(max(normal_coordinates)-SOURCE_WIDTH/2)>1e-8:
        raise ValueError('source solid width/centerline does not match measured type')
    edge_consistency(profile['graphs']['103'])
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
    fields=result['graphs']['102']['objects'][0]['fields']
    replace_field('102',0,fields,'m_keyRefOffset',width_feet/2)
    return result,{'width_feet':width_feet,'source_width_feet':SOURCE_WIDTH,'normal_axis':axis,
        'changes':changes,'edge_consistency':edge_consistency(result['graphs']['103']),
        'requires_existing_type_width_validation':width_feet!=SOURCE_WIDTH}


def encode_wall(profile,new_id,*,width_feet=SOURCE_WIDTH,height_feet=15.0,length_feet,translation_xy,context,
                yaw_degrees=0,room_bounding=None,acknowledge_bounding_hypothesis=False,acknowledge_pending_type_remap=False):
    if width_feet!=SOURCE_WIDTH and not acknowledge_pending_type_remap:
        raise ValueError('changed width requires explicit acknowledgment of pending existing-type-width validation/remapping')
    changed,width_audit=thickness_profile(profile,width_feet)
    bodies,graphs,audit=height_encode(changed,new_id,height_feet=height_feet,length_feet=length_feet,
        translation_xy=translation_xy,context=context,yaw_degrees=yaw_degrees,room_bounding=room_bounding,
        acknowledge_bounding_hypothesis=acknowledge_bounding_hypothesis)
    if width_feet!=SOURCE_WIDTH:audit['thickness']=width_audit
    return bodies,graphs,audit
