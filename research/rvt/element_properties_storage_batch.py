"""Own-schema multiple-owner registration and explicit attached-entity hypothesis."""
from copy import deepcopy
from collections import deque
import struct,uuid
from element_properties_storage import register_schema_and_owner,SCHEMA_GUID,SCHEMA_NAME,metadata_values,guid
from element_properties import declarations_for,normalized_objects
from wall_element import GraphEncoder


def register_schema_and_owners(raw,graph,declarations,owner_ids):
    if not isinstance(owner_ids,list)or not owner_ids or any(type(i)is not int or not 0<i<2**31 for i in owner_ids):raise ValueError('bounded positive owners required')
    if owner_ids!=sorted(set(owner_ids)):raise ValueError('owners must be sorted unique')
    _,expected,changes=register_schema_and_owner(raw,graph,declarations,owner_ids[0])
    targets={'ESSchemaStorage','EStorageTracking','ElemsSetWithCellsTracking'}
    original=[o for o in graph['objects']if o['class_name']in targets]
    revised=[o for o in expected['objects']if o['class_name']in targets]
    # The first-owner operation proves exact source reconstruction and map shape.
    source_tracking=next(o for o in original if o['class_name']=='ElemsSetWithCellsTracking')['fields']['m_elemIdSetMap']
    source_ids={v['m_id']['m_id64']for row in source_tracking for v in row['second']['m_idSet']}
    if source_ids.intersection(owner_ids):raise ValueError('owner already has tracked cells')
    byname={o['class_name']:o for o in revised}
    tracking=byname['EStorageTracking']['fields']['m_trackingItems']
    own=bytes(uuid.UUID(SCHEMA_GUID).bytes_le)
    entry=next(r for r in tracking if bytes(r['m_schemaGuid']['m_guid']['guid_bytes'])==own)
    entry['m_elemIdSet']=[{'m_id':{'m_id64':i}}for i in owner_ids]
    cells=byname['ElemsSetWithCellsTracking']['fields']['m_elemIdSetMap']
    ids=next(r for r in cells if r['first']==-100)['second']['m_idSet']
    for i in owner_ids[1:]:ids.append({'m_id':{'m_id64':i}})
    ids.sort(key=lambda v:v['m_id']['m_id64'])
    encoder=GraphEncoder(declarations_for(declarations,[{'objects':original}]))
    patches=[]
    for before,after,change in zip(original,revised,changes):
        encoded=encoder.fields(after['class_tag'],after['fields'])
        patches.append((before['start'],before['fields_end'],encoded));change['new_bytes']=len(encoded)
    result=raw
    for start,end,value in sorted(patches,reverse=True):result=result[:start]+value+result[end:]
    return result,expected,changes


class OwnEncoder(GraphEncoder):
    def fields(self,tag,values):
        if self.classes[tag]['name']=='ESEntity':
            blob=values['m_blob']
            if set(values)!={'m_blob'}or blob!={'discriminator':-1,'schema_guid':SCHEMA_GUID,'state':'serialized_present'}:raise ValueError('only own present entity supported')
            return struct.pack('<i',-1)+uuid.UUID(SCHEMA_GUID).bytes_le
        return super().fields(tag,values)


def attach(graph,declarations,source_body,application_id,name,properties,*,acknowledge_hypotheses=False):
    """Attach own entity using existing common Element cell-list framing.

    Requires a fully decoded graph with exact edges and source bytes. Existing ES
    entities are rejected; this does not infer native lifecycle acceptance.
    """
    if not acknowledge_hypotheses:raise ValueError('explicit attached entity lifecycle hypothesis acknowledgment required')
    if not graph.get('objects')or graph['objects'][0]['class_name']not in ('DirectShape','SWall'):raise ValueError('only explicit DirectShape/SWall owners supported')
    if any(o['class_name']in ('ESEntityCell','ExtensibleStorageEntity')for o in graph['objects']):raise ValueError('existing entities require separate migration policy')
    before=GraphEncoder(declarations_for(declarations,[graph]))
    if before.graph(graph)!=source_body:raise ValueError('source graph does not reconstruct byte-exactly')
    values=metadata_values(application_id,name,properties)
    changed=deepcopy(graph);objects=changed['objects'];original_count=len(objects)
    classes={c['name']:c for c in declarations}
    for cname,tag in [('CellList',723),('ESEntity',1330),('ESEntityCell',1331)]:
        if classes.get(cname,{}).get('tag')!=tag:raise ValueError('requires measured2024 cell classes')
    def obj(cname,fields):return {'class_name':cname,'class_tag':classes[cname]['tag'],'token':0xffffffff,'fields':fields}
    adjacency={i:[]for i in range(len(objects))}
    for edge in graph['edges']:
        s,t=edge['source_object_index'],edge['target_object_index']
        if not 0<=s<original_count or not 0<=t<original_count:raise ValueError('invalid source edge')
        adjacency[s].append((edge['pointer_offset'],t))
    pointer=objects[0]['fields']['m_cellList']
    if pointer['pointer_token']==0:
        if pointer['class_tag']is not None:raise ValueError('invalid null cell pointer')
        cell_index=len(objects);objects.append(obj('CellList',{'m_cells':[]}));adjacency[cell_index]=[]
        adjacency[0].append((pointer['offset'],cell_index))
        pointer.update(pointer_token=0xffffffff,class_tag=723)
    else:
        matches=[e for e in graph['edges']if e['source_object_index']==0 and e['pointer_offset']==pointer['offset']]
        if pointer['pointer_token']!=0xffffffff or len(matches)!=1:raise ValueError('requires owned cell list')
        cell_index=matches[0]['target_object_index']
        if objects[cell_index]['class_name']!='CellList':raise ValueError('cell pointer class mismatch')
    cell=objects[cell_index]
    es_index=len(objects);objects.append(obj('ESEntityCell',{'m_entityMap':[{'first':guid(SCHEMA_GUID),'second':{'m_blob':{'discriminator':-1,'schema_guid':SCHEMA_GUID,'state':'serialized_present'}}}]}))
    cell['fields']['m_cells'].append({'pointer_token':0xffffffff,'class_tag':1331})
    adjacency[cell_index].append((max([p for p,_ in adjacency[cell_index]],default=-1)+1,es_index))
    entity_index=len(objects)
    objects.append({'class_name':'ExtensibleStorageEntity','class_tag':0,'token':0xffffffff,'fields':{'schema_guid':SCHEMA_GUID,'schema_name':SCHEMA_NAME,'values':values}})
    adjacency[es_index]=[(0,entity_index)];adjacency[entity_index]=[]
    queue=deque([0]);seen={0};ordered=[]
    while queue:
        i=queue.popleft();ordered.append(objects[i])
        for _,target in sorted(adjacency[i]):
            if target not in seen:seen.add(target);queue.append(target)
    if len(seen)!=len(objects):raise ValueError('unreachable source object')
    encoder=OwnEncoder(declarations_for(declarations,[{'objects':[o for o in objects if o['class_tag']]}]))
    data=struct.pack('<H',objects[0]['class_tag'])
    for o in ordered:
        if o['class_tag']==0:
            for v in values:
                raw=v.encode('utf-16-le');data+=struct.pack('<I',len(raw)//2)+raw
        else:data+=encoder.fields(o['class_tag'],o['fields'])
    return data,{'source_object_count':original_count,'attached_object_count':len(ordered),'schema_guid':SCHEMA_GUID,
                 'owner_class':objects[0]['class_name'],'hypothesis':'Own ES entity attachment uses common Element CellList; native lifecycle unvalidated',
                 'expected_original_objects':normalized_objects(graph),'original_cell_list_was_null':graph['objects'][0]['fields']['m_cellList']['pointer_token']==0}
