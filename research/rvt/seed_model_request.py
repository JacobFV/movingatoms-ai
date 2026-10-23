"""Bounded SI mesh document request. No geometry is silently omitted."""
from copy import deepcopy
import json
from seed_document_request import number,label


def validate(request):
    if not isinstance(request,dict)or set(request)!={'schema_version','units','levels','elements'}:
        raise ValueError('requires schema_version, units, levels and elements only')
    if type(request['schema_version'])is not int or request['schema_version']!=1 or request['units']!='metres':
        raise ValueError('only schema_version1 and metres supported')
    if not isinstance(request['levels'],list)or len(request['levels'])>100:raise ValueError('at most100 levels supported')
    levels=[];level_ids=set();names=set()
    for level in request['levels']:
        if not isinstance(level,dict)or set(level)!={'id','name','elevation'}:raise ValueError('level requires id/name/elevation')
        ident=label(level['id'],'level id');name=label(level['name'],'level name')
        elevation=number(level['elevation'],-1000,1000,'level elevation')
        if ident in level_ids or name.casefold()in names:raise ValueError('duplicate level id/name')
        if name.casefold()=='level 1'and(name!='Level 1'or elevation!=0):raise ValueError('reserved seed Level 1 requires exact name and elevation0')
        level_ids.add(ident);names.add(name.casefold())
        levels.append({'id':ident,'name':name,'elevation':elevation,'reuse_seed':name=='Level 1'})
    if not isinstance(request['elements'],list)or not 1<=len(request['elements'])<=100:raise ValueError('requires1..100 mesh elements')
    elements=[];ids=set();vertices=triangles=0
    for element in request['elements']:
        required={'id','name','category','properties','parts'}
        if not isinstance(element,dict)or not required<=set(element)or set(element)-(required|{'level_id'}):raise ValueError('unsupported element fields')
        ident=label(element['id'],'element id');name=label(element['name'],'element name');category=label(element['category'],'category')
        if ident in ids:raise ValueError('duplicate element id')
        ids.add(ident)
        level_id=element.get('level_id')
        if 'level_id'in element and(not isinstance(level_id,str)or level_id not in level_ids):raise ValueError('level_id must reference requested level')
        props=element['properties']
        if not isinstance(props,dict):raise ValueError('properties must be JSON object')
        def safe(value):
            if value is None or type(value)in(bool,int):return
            if type(value)is float:number(value,-1e300,1e300,'property number');return
            if isinstance(value,str):
                if '\0'in value:raise ValueError('NUL in property')
                value.encode('utf-16-le');return
            if isinstance(value,list):
                for item in value:safe(item)
                return
            if isinstance(value,dict):
                for key,item in value.items():
                    if not isinstance(key,str):raise ValueError('property keys must be strings')
                    safe(key);safe(item)
                return
            raise ValueError('properties must be finite JSON values')
        try:safe(props)
        except(UnicodeEncodeError,RecursionError)as error:raise ValueError('invalid or excessive property nesting')from error
        if len(json.dumps(props,ensure_ascii=False,allow_nan=False).encode('utf-16-le'))>1000000:raise ValueError('property payload exceeds1MB')
        parts=element['parts']
        if not isinstance(parts,list)or not 1<=len(parts)<=100:raise ValueError('requires1..100 explicit parts')
        checked=[]
        for part in parts:
            if not isinstance(part,dict)or set(part)!={'vertices','triangles'}:raise ValueError('part requires vertices/triangles only')
            points=part['vertices'];faces=part['triangles']
            if not isinstance(points,list)or not points or not isinstance(faces,list)or not faces:raise ValueError('nonempty mesh arrays required')
            vertices+=len(points);triangles+=len(faces)
            if vertices>100000 or triangles>200000:raise ValueError('document mesh budget exceeded')
            pts=[]
            for p in points:
                if not isinstance(p,list)or len(p)!=3:raise ValueError('XYZ vertex required')
                pts.append([number(v,-10000,10000,'world coordinate')for v in p])
            for face in faces:
                if not isinstance(face,list)or len(face)!=3 or any(type(i)is not int or not 0<=i<len(points)for i in face):raise ValueError('triangle index outside explicit part')
            checked.append({'vertices':pts,'triangles':deepcopy(faces)})
        elements.append({'id':ident,'name':name,'category':category,'properties':deepcopy(props),'level_id':level_id,'parts':checked})
    if sum(not x['reuse_seed']for x in levels)+len(elements)>100:raise ValueError('at most100 new native elements supported')
    return {'schema_version':1,'units':'metres','levels':levels,'elements':elements}
