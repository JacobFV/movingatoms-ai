"""Explicit metre-based request contract for a bounded native-seed document."""
import math

FEET_PER_METRE=1/0.3048


def number(value,low,high,label):
    if type(value)not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError(f'{label} must be finite within {low}..{high}')
    return float(value)


def label(value,kind):
    if not isinstance(value,str) or not value or value!=value.strip() or '\0' in value or len(value)>128:
        raise ValueError(f'{kind} requires a trimmed nonempty name of at most128 characters')
    try:value.encode('utf-16-le')
    except UnicodeEncodeError as error:raise ValueError('invalid Unicode name')from error
    return value


def validate(request):
    if not isinstance(request,dict) or set(request)!={'schema_version','units','levels','walls'}:
        raise ValueError('requires schema_version, units, levels and walls only')
    if type(request['schema_version'])is not int or request['schema_version']!=1 or request['units']!='metres':
        raise ValueError('only schema_version1 and metres supported')
    if not isinstance(request['levels'],list) or not 1<=len(request['levels'])<=100:
        raise ValueError('requires 1..100 requested levels')
    levels=[];names=set()
    for value in request['levels']:
        if not isinstance(value,dict)or set(value)!={'name','elevation'}:raise ValueError('level requires name and elevation only')
        name=label(value['name'],'level');elevation=number(value['elevation'],-1000,1000,'level elevation')
        if name.casefold()in names:raise ValueError('level names must be unique ignoring case')
        if name.casefold()=='level 1' and (name!='Level 1' or elevation!=0):
            raise ValueError('seed Level 1 can only be reused under its exact name at elevation0')
        names.add(name.casefold());levels.append({'name':name,'elevation':elevation,'reuse_seed':name=='Level 1'})
    byname={level['name']:level for level in levels}
    if not isinstance(request['walls'],list)or not 1<=len(request['walls'])<=100:raise ValueError('requires 1..100 walls')
    walls=[];identifiers=set()
    required={'id','base_level','top_level','start','length','height'}
    optional={'yaw_degrees','thickness','kind'}
    for value in request['walls']:
        if not isinstance(value,dict)or not required<=set(value)or set(value)-(required|optional):
            raise ValueError('wall fields must match the bounded straight-wall contract')
        ident=label(value['id'],'wall id')
        if ident in identifiers:raise ValueError('wall request IDs must be unique')
        identifiers.add(ident)
        base,top=value['base_level'],value['top_level']
        if not isinstance(base,str)or not isinstance(top,str)or base not in byname or top not in byname:
            raise ValueError('wall levels must reference exact requested names')
        if byname[top]['elevation']<=byname[base]['elevation']:raise ValueError('wall top level must lie above base level')
        if value.get('kind','straight')!='straight':raise ValueError('only straight walls supported')
        thickness=number(value.get('thickness',0.2),0.2,0.2,'wall thickness')
        start=value['start']
        if not isinstance(start,list)or len(start)!=2:raise ValueError('world start requires two metre coordinates')
        walls.append({'id':ident,'base_level':base,'top_level':top,
            'start':[number(x,-10000,10000,'world coordinate')for x in start],
            'length':number(value['length'],0.01,1000,'wall length'),
            'height':number(value['height'],0.01,1000,'wall height'),
            'yaw_degrees':number(value.get('yaw_degrees',0),-360,360,'absolute wall yaw'),
            'thickness':thickness,'kind':'straight'})
    if sum(not level['reuse_seed']for level in levels)+len(walls)>100:raise ValueError('at most100 new native elements supported')
    return {'schema_version':1,'units':'metres','levels':levels,'walls':walls}
