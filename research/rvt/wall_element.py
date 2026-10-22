"""Schema-driven re-encoding of a measured straight-wall graph profile.

Supports a translated instance using explicitly retained type/level/material
context. This is neither an arbitrary wall authoring engine nor a native-save
acceptance claim. No opaque body bytes are cloned.
"""
from collections import Counter
from copy import deepcopy
import math
import struct


class GraphEncoder:
    def __init__(self,declarations):
        self.classes={c['tag']:c for c in declarations}
        if len(self.classes)!=len(declarations) or len({c['name'] for c in declarations})!=len(declarations):
            raise ValueError('duplicate class identity')
        def check_field(field):
            if field['uninterpreted_flags']:raise ValueError('unsupported field flags')
            if any(r['tag'] not in self.classes for r in field['references']):raise ValueError('unknown field class')
            if field['nested_descriptor']:check_field(field['nested_descriptor'])
        for c in declarations:
            for field in c['fields']:check_field(field)
        self.layouts={}
        for tag in self.classes:
            chain=[];seen=set();at=tag
            while at:
                if at in seen:raise ValueError('inheritance cycle')
                if at not in self.classes:raise ValueError('unknown parent')
                seen.add(at);c=self.classes[at];chain.append(c);at=c['parent_reference']['tag']
            fields=[(c,f) for c in reversed(chain) for f in c['fields'] if not f['uninterpreted_flags']&2]
            names=Counter(f['name'] for _,f in fields)
            self.layouts[tag]=[(f"{c['name']}::{f['name']}" if names[f['name']]>1 else f['name'],c,f) for c,f in fields]
            if len({name for name,_,_ in self.layouts[tag]})!=len(fields):raise ValueError('duplicate qualified field')

    def fields(self,tag,values):
        if tag not in self.layouts:raise ValueError('unknown object class')
        layout=self.layouts[tag]
        if set(values)!={name for name,_,_ in layout}:raise ValueError('schema fields mismatch '+self.classes[tag]['name'])
        result=[]
        for name,c,f in layout:
            if f['uninterpreted_flags']:
                raise ValueError('unmeasured stored field flags')
            if c['name']=='ClassDefinitionRef' and f['name']=='m_ref':
                tag=values[name]['class_tag']
                if self.classes.get(tag,{}).get('name')!=values[name]['class_name']:raise ValueError('class reference differs')
                result.append(struct.pack('<H',tag))
            else:result.append(self.field(f,values[name]))
        return b''.join(result)

    def field(self,f,value):
        base,modifier=f['base'],f['modifier']
        if modifier in (0x10,0x11,0x12,0x13,0x50,0x51,0x52,0x53):
            if not isinstance(value,list):raise ValueError('array required')
            if modifier<0x50:
                if len(value)!=f['array_count']:raise ValueError('fixed array length differs')
                prefix=b''
            else:prefix=struct.pack('<I',len(value))
            sub=dict(f,modifier=modifier&15,array_count=None)
            return prefix+b''.join(self.field(sub,v) for v in value)
        if modifier in (1,2,3) and base==14:
            token=value['pointer_token'];tag=value['class_tag']
            out=struct.pack('<I',token)
            if token and modifier!=3:
                if tag not in self.classes:raise ValueError('unknown pointer class')
                out+=struct.pack('<H',tag)
            elif tag is not None:raise ValueError('null/external pointer has class tag')
            return out
        if modifier==0x60 and base==8:
            if not isinstance(value,str) or '\0' in value:raise ValueError('invalid string')
            raw=value.encode('utf-16le');return struct.pack('<I',len(raw)//2)+raw
        if modifier:raise ValueError(f'unsupported modifier {modifier}')
        if base==14:
            if len(f['references'])!=1:raise ValueError('ambiguous inline class')
            return self.fields(f['references'][0]['tag'],value)
        if base==13:
            if not f['nested_descriptor']:raise ValueError('missing nested descriptor')
            return self.field(f['nested_descriptor'],value)
        if base==1:
            if type(value)is not bool:raise ValueError('bool required')
            return bytes([value])
        if base in (2,3,4,5,11):
            if type(value)is not int:raise ValueError('integer required')
            return struct.pack({2:'<B',3:'<h',4:'<i',5:'<I',11:'<q'}[base],value)
        if base in (6,7):
            if type(value)not in (int,float) or not math.isfinite(value):raise ValueError('finite scalar required')
            return struct.pack('<f' if base==6 else '<d',value)
        if base==9:
            raw=bytes(value['guid_bytes'])
            if len(raw)!=16:raise ValueError('GUID width')
            return raw
        raise ValueError(f'unsupported scalar {base}')

    def graph(self,graph):
        objects=graph['objects']
        if not objects:raise ValueError('empty graph')
        return struct.pack('<H',objects[0]['class_tag'])+b''.join(self.fields(o['class_tag'],o['fields']) for o in objects)


def translated_wall(profile,new_id,translation_xy,context,*,room_bounding=None,acknowledge_bounding_hypothesis=False):
    """Translate measured straight wall in XY; retain audited levels and shape.

    Direction vectors, UVs, curve end parameters, plane domains, topology,
    empty-cache boxes and reference-plane flags remain unchanged.
    """
    if type(new_id)is not int or not 0<new_id<2**31 or new_id==20826:
        raise ValueError('fresh ID must fit measured geometry-tag int32')
    if len(translation_xy)!=2 or any(type(v)not in (int,float) or not math.isfinite(v) for v in translation_xy):
        raise ValueError('finite XY translation required')
    if context!=profile['external_references']:
        raise ValueError('explicit existing context must match audited profile')
    if room_bounding is not None:
        if type(room_bounding)is not bool:raise ValueError('room bounding must be boolean')
        if not acknowledge_bounding_hypothesis:raise ValueError('explicit bounding-toggle hypothesis acknowledgment required')
        for class_name,field_name in [('HostObj','m_roomBounding'),('AnalyticalSpaceBoundingCell','m_isSpaceBounding')]:
            classes=[c for c in profile['declarations'] if c['name']==class_name]
            if len(classes)!=1:raise ValueError('bounding class missing')
            fields=[f for f in classes[0]['fields'] if f['name']==field_name]
            if len(fields)!=1 or fields[0]['raw_descriptor']!=1 or fields[0]['uninterpreted_flags']:
                raise ValueError('bounding field is not observed serialized boolean')
    graphs=deepcopy(profile['graphs']);moves=[];identities=[]
    for channel,graph in graphs.items():
        for i,obj in enumerate(graph['objects']):
            fields=obj['fields'];name=obj['class_name']
            if channel=='101' and name=='ElementParents':
                for item in fields['m_deletion']:
                    if item['m_id']['m_id64']==20826:item['m_id']['m_id64']=new_id;identities.append((channel,i,'m_deletion.self'))
            if channel=='102' and name=='SWall':
                if fields['m_id']['m_id']['m_id64']!=20826:raise ValueError('source root ID differs')
                fields['m_id']['m_id']['m_id64']=new_id;identities.append((channel,i,'m_id'))
            if channel=='103' and i==0:
                if name!='GElement' or fields['m_elementId']!=20826 or fields['m_GInfo']['m_tag']!=20826:raise ValueError('source geometry owner differs')
                fields['m_elementId']=new_id;fields['m_GInfo']['m_tag']=new_id
                identities.extend([(channel,i,'m_elementId'),(channel,i,'m_GInfo.m_tag')])
            if room_bounding is not None and channel=='102':
                if name=='SWall':fields['m_roomBounding']=room_bounding
                if name=='AnalyticalSpaceBoundingCell':fields['m_isSpaceBounding']=room_bounding
            keys=[]
            if name in ('Plane','GLine'):keys=['m_origin']
            if channel=='101' and name=='Outline':keys=['m_minmax']
            if channel=='103' and i==0:keys=['m_bBox','m_tightbBox']
            for key in keys:
                old=deepcopy(fields[key]);value=fields[key]
                points=value if key in ('m_minmax','m_bBox','m_tightbBox') else [value]
                for point in points:
                    if len(point)!=3:raise ValueError('expected world XYZ point')
                    point[0]+=translation_xy[0];point[1]+=translation_xy[1]
                moves.append({'channel':int(channel),'object':i,'class':name,'field':key,'before':old,'after':deepcopy(value)})
    if len(identities)!=4:raise ValueError('unexpected self identity count')
    encoder=GraphEncoder(profile['declarations'])
    return {int(channel):encoder.graph(graph) for channel,graph in graphs.items()},graphs,moves,identities
