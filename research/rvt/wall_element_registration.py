"""Append to measured StructuralElemSetTracking; not a topology regeneration."""
from copy import deepcopy
import hashlib
from new_element_registration import extended_set,semantic_graph


def register(raw,evidence,new_id,source_id=20826):
    if hashlib.sha256(raw).hexdigest()!=evidence['inflated_sha256']:raise ValueError('Global/Latest hash differs')
    if type(new_id)is not int or not 0<new_id<2**31 or new_id==source_id:raise ValueError('invalid fresh wall ID')
    obj=evidence['object']
    if obj['class_name']!='StructuralElemSetTracking':raise ValueError('wrong tracker')
    spans=[s for s in obj['field_spans'] if s['name']=='m_elemIdSet']
    if len(spans)!=1:raise ValueError('ambiguous ID set')
    values=[v['m_id']['m_id64'] for v in obj['fields']['m_elemIdSet']]
    if source_id not in values:raise ValueError('source not registered')
    start,end,replacement=extended_set(raw,spans[0],values,new_id)
    return raw[:start]+replacement+raw[end:],{'span_before':spans[0],'ids_before':values,'ids_after':sorted(values+[new_id])}


def verify_graph(before,after,change):
    expected=semantic_graph(before)
    objs=[o for o in expected['objects'] if o['class_name']=='StructuralElemSetTracking']
    if len(objs)!=1:raise ValueError('ambiguous tracker graph')
    objs[0]['fields']['m_elemIdSet']=[{'m_id':{'m_id64':v}} for v in change['ids_after']]
    if expected!=semantic_graph(after):raise ValueError('unexpected global semantic change')
    return True
