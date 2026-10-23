"""Measured native wall Comments encoding; not arbitrary parameter declaration."""
from copy import deepcopy
from wall_element import GraphEncoder

COMMENTS=-1010106


def declarations_for(declarations,graphs,extra_names=()):
    classes={c['tag']:c for c in declarations};names={c['name']:c['tag'] for c in declarations}
    queue=[o['class_tag'] for g in graphs for o in g['objects']]+[names[n] for n in extra_names];seen=set()
    def refs(field):
        out=[r['tag'] for r in field['references']]
        if field['nested_descriptor']:out+=refs(field['nested_descriptor'])
        return out
    while queue:
        tag=queue.pop()
        if tag in seen:continue
        if tag not in classes:raise ValueError('missing property dependency class')
        seen.add(tag);c=classes[tag]
        if c['parent_reference']['tag']:queue.append(c['parent_reference']['tag'])
        queue.extend(t for f in c['fields'] for t in refs(f))
    return [classes[tag] for tag in sorted(seen)]


def normalized_objects(graph):
    def clean(value):
        if isinstance(value,list):return [clean(v) for v in value]
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k!='offset'}
        return value
    return [{'class_tag':o['class_tag'],'class_name':o['class_name'],'token':o['token'],'fields':clean(o['fields'])}
            for o in graph['objects']]


def set_comments(graph,declarations,value,*,expected=None,allow_create=False):
    """Write only measured built-in instance Comments; do not repurpose as metadata.

    Returns serialized body and expected object semantics. Offsets/edge indices
    must be reconstructed by decoding the returned body, never copied as valid.
    """
    if not isinstance(value,str) or '\0' in value or len(value.encode('utf-16-le'))//2>32767:
        raise ValueError('Comments requires bounded NUL-free UTF-16 text')
    if not graph['objects'] or graph['objects'][0]['class_name']!='SWall' or graph['objects'][0]['class_tag']!=3669:
        raise ValueError('requires measured 2024 SWall profile')
    classes={c['name']:c for c in declarations}
    if classes.get('ParamValueSetAString',{}).get('tag')!=3021 or classes.get('ParamValueAString',{}).get('tag')!=3017:
        raise ValueError('requires measured string parameter classes')
    expected_layouts={'ParamValueSetAString':[('m_paramSet',0x500e,[3017])],
                      'ParamValueAString':[('m_paramId',0xe,[20]),('m_value',0x6008,[])]}
    for name,layout in expected_layouts.items():
        c=classes[name]
        actual=[(f['name'],f['raw_descriptor'],[r['tag']for r in f['references']])for f in c['fields']]
        if c['parent_reference']['tag'] or actual!=layout:
            raise ValueError('string parameter declaration differs from measured profile')
    encoder=GraphEncoder(declarations);encoder.graph(graph)
    changed=deepcopy(graph);root=changed['objects'][0];ptr=root['fields']['m_pParamValueSetAString']
    sets=[(i,o) for i,o in enumerate(changed['objects']) if o['class_name']=='ParamValueSetAString']
    if ptr['pointer_token']==0:
        if sets or ptr['class_tag'] is not None or not allow_create or expected is not None:
            raise ValueError('absent Comments requires explicit creation and no old-value expectation')
        following=[e for e in changed['edges'] if e['source_object_index']==0 and e['pointer_offset']>ptr['offset']]
        if not following:raise ValueError('unmeasured terminal parameter insertion position')
        at=min(following,key=lambda e:e['pointer_offset'])['target_object_index']
        if not 1<=at<len(changed['objects']):raise ValueError('invalid parameter insertion position')
        ptr.update(pointer_token=0xffffffff,class_tag=3021)
        obj={'class_name':'ParamValueSetAString','class_tag':3021,'token':0xffffffff,
             'fields':{'m_paramSet':[{'m_paramId':{'m_id':{'m_id64':COMMENTS}},'m_value':value}]}}
        changed['objects'].insert(at,obj);mode='created_measured_string_container'
    else:
        if ptr['pointer_token']!=0xffffffff or ptr['class_tag']!=3021 or len(sets)!=1:
            raise ValueError('unsupported shared/ambiguous string set')
        at,obj=sets[0]
        edges=[e for e in graph['edges'] if e['pointer_offset']==ptr['offset'] and e['source_object_index']==0]
        if len(edges)!=1 or edges[0]['target_object_index']!=at:raise ValueError('string-set ownership mismatch')
        pairs=obj['fields']['m_paramSet'];hits=[p for p in pairs if p['m_paramId']['m_id']['m_id64']==COMMENTS]
        if len(hits)!=1 or hits[0]['m_value']!=expected:raise ValueError('existing Comments precondition differs')
        hits[0]['m_value']=value;mode='updated_existing_comments'
    return encoder.graph(changed),normalized_objects(changed),{'parameter_id':COMMENTS,'mode':mode,
          'utf16_code_units':len(value.encode('utf-16-le'))//2,'arbitrary_application_metadata_supported':False}
