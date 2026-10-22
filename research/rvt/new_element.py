"""Bounded DataStorage payload encoder from file-local embedded schema.

This encodes three bodies, not a complete save. The supported profile retains
observed header flags and two existing Extensible Storage schema dependencies.
No source object bytes, opaque IDs, or references are cloned.
"""
from dataclasses import replace
import struct
import uuid
import element_table
import save_history

FDX = '8de41042-7da6-4d45-afb4-f8e5ba779816'
UNIQUE = '4147c867-cdfe-42fd-808f-3bbafda73da5'


class Encoder:
    """Small fail-closed subset of the embedded field descriptors."""
    def __init__(self, declarations):
        self.classes = {c['tag']:c for c in declarations}
        self.names = {c['name']:c['tag'] for c in declarations}
        if len(self.classes) != len(declarations): raise ValueError('duplicate class tags')
        if len(self.names) != len(declarations): raise ValueError('duplicate class names')
        self.layouts = {}
        for tag in self.classes:
            chain=[];seen=set();current=tag
            while current:
                if current in seen: raise ValueError('inheritance cycle')
                if current not in self.classes: raise ValueError('unknown parent class')
                seen.add(current);c=self.classes[current];chain.append(c)
                for f in c['fields']:
                    if any(r['tag'] not in self.classes for r in f['references']):
                        raise ValueError('unknown field class reference')
                current=c['parent_reference']['tag']
            flattened=[f for c in reversed(chain) for f in c['fields']]
            if len({f['name'] for f in flattened})!=len(flattened):
                raise ValueError('duplicate inherited field name')
            self.layouts[tag]=flattened

    def tag(self, name): return self.names[name]

    def fields(self, tag, values):
        c = self.classes[tag]
        descriptors = self.layouts[tag]
        if set(values) != {f['name'] for f in descriptors}:
            raise ValueError('schema/model fields disagree: '+c['name'])
        return b''.join(self.field(f, values[f['name']]) for f in descriptors)

    def field(self, f, value):
        if f['uninterpreted_flags'] or f['array_count'] is not None or f['nested_descriptor']:
            raise ValueError('unsupported field flags/array/descriptor')
        d = f['raw_descriptor']
        if d in (0x500e,0x510e):
            if not isinstance(value,list): raise ValueError('array required')
            sub = dict(f,raw_descriptor=0xe if d==0x500e else 0x10e)
            return struct.pack('<I',len(value))+b''.join(self.field(sub,v) for v in value)
        if d == 0xe:
            if len(f['references'])!=1: raise ValueError('ambiguous embedded class')
            return self.fields(f['references'][0]['tag'],value)
        if d in (0x10e,0x30e):
            token=value['token']
            result=struct.pack('<I',token)
            if token==0xffffffff:
                if 'schema_guid' in value: result+=uuid.UUID(value['schema_guid']).bytes_le
                else: result+=struct.pack('<H',self.tag(value['class']))
            elif token not in (0,1): raise ValueError('unsupported pointer token')
            return result
        if d==0x6008:
            if not isinstance(value,str) or '\0' in value: raise ValueError('invalid string')
            raw=value.encode('utf-16le')
            return struct.pack('<I',len(raw)//2)+raw
        if d==9: return uuid.UUID(value).bytes_le
        if d==10: return struct.pack('<H',self.tag(value))
        if d==1:
            if type(value) is not bool: raise ValueError('boolean required')
            return bytes([value])
        if d in (3,4,11):
            if type(value) is not int: raise ValueError('integer required')
            return struct.pack({3:'<h',4:'<i',11:'<q'}[d],value)
        raise ValueError(f'unsupported field descriptor {d:#x}')


def identifier(value): return {'m_id':{'m_id64':value}}
def pointer(name): return {'token':0xffffffff,'class':name}


def validate_catalog(catalog):
    for guid,name,field,kind in ((FDX,'FDXModifiedExchangeList','ModifiedExchangeList','TCHAR'),
                                (UNIQUE,'DataStorageUniqueId','Id','GUIDvalue')):
        schema=catalog['schemas'].get(guid)
        if schema is None or schema['name']!=name or len(schema['fields'])!=1:
            raise ValueError('required file-local ES schema missing')
        f=schema['fields'][0]
        if (f['index'],f['name'],f['type_name'],f['container_type'],f['subschema_guid'],f['spec_type_id']) != (0,field,kind,0,None,None):
            raise ValueError('unsupported file-local ES schema')


def data_storage(declarations,catalog,element_id,name,storage_guid):
    """Construct channel bodies, with no positive reference except self."""
    if type(element_id) is not int or not 0<element_id<2**63-1:
        raise ValueError('element ID must be a positive signed64 value')
    storage_guid=uuid.UUID(str(storage_guid))
    if storage_guid.int==0: raise ValueError('zero storage GUID')
    validate_catalog(catalog)
    e=Encoder(declarations)
    # Restrict to the actual profile independently re-decoded in core2024.
    if (e.tag('DataStorage'),e.tag('ElementHeader'),e.tag('SerializedDummy'))!=(1133,1439,3712):
        raise ValueError('only measured Revit2024 profile supported')
    root={k:{'token':0} for k in ('m_pParamValueSetDouble','m_pParamValueSetInt',
          'm_pParamValueSetAString','m_pParamValueSetElementId','m_geomSteps','m_pGeomTable')}
    root.update(m_constrInfo=[],m_cellList=pointer('CellList'),
                m_docAccess={'m_pDoc':{'token':1}},m_id=identifier(element_id),
                m_locked=False,m_moribund=False,m_dummy=False,m_name=name)
    for key in ('m_assocLevelId','m_famId','m_unplacedOwnerId','m_ownerDBViewId',
                'm_createdPhaseId','m_demolishedPhaseId','m_designOptionId'):
        root[key]=identifier(-1)
    cells={'m_cells':[pointer('ESEntityCell')]}
    entities={'m_entityMap':[{'first':{'m_guid':guid},'second':{'m_blob':{'token':0xffffffff,'schema_guid':guid}}}
                            for guid in (FDX,UNIQUE)]}
    body=struct.pack('<H',e.tag('DataStorage'))+e.fields(e.tag('DataStorage'),root)
    body+=e.fields(e.tag('CellList'),cells)+e.fields(e.tag('ESEntityCell'),entities)
    body+=struct.pack('<I',0)+storage_guid.bytes_le
    header={'m_regenHistory':{'m_historyMap':[]},'m_viewRules':{'m_nVisibleViewFlags':-4225},
            'm_abFlags4Bytes':8206,'m_classDef':{'m_ref':'DataStorage'},
            'm_pBBox':{'token':0},'m_parents':pointer('ElementParents')}
    for key in ('m_categroryId','m_familyId','m_ownerViewId','m_designOptionId','m_unplacedOwnerId','m_miscId'):
        header[key]=identifier(-1)
    parents={k:[] for k in ('m_regenOnly','m_regenWildcards','m_nonDetermRegenChildren',
              'm_dependencyParents','m_appearanceParents','m_deferredParents',
              'm_deferredPropagationParents','m_computedParametersParents')}
    parents.update(m_deletion=[identifier(element_id)],m_hasNonDetermRegenChildren=False)
    head=struct.pack('<H',e.tag('ElementHeader'))+e.fields(e.tag('ElementHeader'),header)
    head+=e.fields(e.tag('ElementParents'),parents)
    dummy=struct.pack('<H',e.tag('SerializedDummy'))+e.fields(e.tag('SerializedDummy'),{})
    return {101:head,102:body,103:dummy}


def allocate_identity(table,history):
    """Bounded fresh row allocation; new History episode must be appended by caller.

    Sets all three episode fields to the new creation episode, matching observed
    newly-created DataStorage 80437. Whether this suffices in a native save is
    unverified. Leaves all existing rows untouched.
    """
    element_table.validate(table)
    save_history.encode(history)
    if history.next_sequence!=len(history.episodes) or history.subsequence_deficit:
        raise ValueError('unsupported creation episode allocation')
    if table.width!=8: raise ValueError('only signed64 profile supported')
    ident=table.last_id+1;episode=history.next_sequence
    if not 0<ident<2**63-1 or not 0<=episode<2**31:
        raise ValueError('allocator bounds exceeded')
    row=struct.pack('<QIIIQQI',ident,episode,episode,episode,ident,2**64-1,0)
    trailer=bytearray(table.trailer);struct.pack_into('<Q',trailer,12,ident)
    result=replace(table,rows=table.rows+(row,),trailer=bytes(trailer))
    element_table.validate(result)
    return ident,result
