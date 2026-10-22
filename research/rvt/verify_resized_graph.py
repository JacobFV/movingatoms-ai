"""Compare full native graphs, permitting one value and its cursor displacement."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def verify(path):
    source=json.loads(path.read_bytes())
    if len(source)!=2:raise ValueError('expected original and edited graphs')
    before,after=[x['graph'] for x in source]
    expected=copy.deepcopy(before)
    matches=[(i,p) for i,o in enumerate(expected['objects'])
             for p in o['fields'].get('m_paramSet',[])
             if p.get('m_paramId',{}).get('m_id',{}).get('m_id64')==-1006903]
    if len(matches)!=1:raise ValueError('target parameter not unique')
    index,param=matches[0]
    if param['m_value']!='Wood':raise ValueError('unexpected original value')
    value='Polished concrete';param['m_value']=value
    delta=len(value.encode('utf-16le'))-8
    # The containing parameter object is resized; later objects move by delta.
    boundary=before['objects'][index]['fields_end']
    expected['consumed_bytes']+=delta
    for i,o in enumerate(expected['objects']):
        if i>index:o['start']+=delta
        if i>=index:o['fields_end']+=delta
    shifted_pointers=0
    def adjust(value):
        nonlocal shifted_pointers
        if isinstance(value,dict):
            if set(value)=={'class_tag','offset','pointer_token'} and value['offset']>=boundary:
                value['offset']+=delta;shifted_pointers+=1
            for child in value.values():adjust(child)
        elif isinstance(value,list):
            for child in value:adjust(child)
    for o in expected['objects']:adjust(o['fields'])
    for edge in expected['edges']:
        if edge['pointer_offset']>=boundary:edge['pointer_offset']+=delta
    if expected!=after:raise ValueError('full graph differs beyond intended value/cursor shifts')
    return {'reader_commit':source[0]['reader_commit'],'complete_objects':len(before['objects']),
            'resolved_pointer_edges':len(before['edges']),'body_growth_bytes':delta,
            'shifted_pointer_locations':shifted_pointers,'one_parameter_value_changed':True,
            'all_other_graph_values_and_pointer_targets_identical':True,
            'original_bytes_consumed':before['consumed_bytes'],'edited_bytes_consumed':after['consumed_bytes'],
            'graph_evidence_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('graphs',type=Path)
    print(json.dumps(verify(p.parse_args().graphs),indent=2))
