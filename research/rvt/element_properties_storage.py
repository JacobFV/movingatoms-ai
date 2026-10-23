"""Fresh Moving Atoms ES schema and owner encoding, an unvalidated save hypothesis."""
from copy import deepcopy
import json,struct,uuid
from element_properties import declarations_for
from wall_element import GraphEncoder
from new_element import Encoder,identifier,pointer

SCHEMA_GUID='3e6dd92d-a1e2-5529-bf69-045c18c5f87b'
SCHEMA_NAME='MovingAtomsElementPropertiesV1'
FIELD_NAMES=('ApplicationId','Name','PropertiesJson')
ZERO='00000000-0000-0000-0000-000000000000'


def guid(value):return {'m_guid':{'guid_bytes':list(uuid.UUID(value).bytes_le)}}


def schema_definition():
    return {'m_guid':guid(SCHEMA_GUID),'m_schemaName':SCHEMA_NAME,
       'm_documentation':'Moving Atoms external element identity and JSON application properties, version 1',
       'm_readAccessLevel':1,'m_writeAccessLevel':1,'m_vendorId':'','m_applicationGUID':guid(ZERO),
       'm_fields':[{'m_entryIndex':i,'m_fieldName':name,'m_fieldTypeName':'TCHAR','m_containerType':0,
                    'm_documentation':'','m_specTypeId':{'m_typeId':''},'m_subSchemaGUID':guid(ZERO)}
                   for i,name in enumerate(FIELD_NAMES)]}


def register_schema_and_owner(raw,graph,declarations,owner_id):
    """Re-encode three owned existing app-info objects; no opaque body cloning.

    Caller must allocate a fresh project ElementId separately. Registration is
    hypothesized from measured map/set layouts; native acceptance is untested.
    """
    if type(owner_id)is not int or not 0<owner_id<2**63-1:raise ValueError('positive owner ID required')
    names={'ESSchemaStorage','EStorageTracking','ElemsSetWithCellsTracking'}
    selected=[o for o in graph['objects']if o['class_name']in names]
    if len(selected)!=3 or {o['class_name']for o in selected}!=names:raise ValueError('requires three unique existing registration objects')
    if any(o['fields']['m_pADoc']['pointer_token']!=1 for o in selected):raise ValueError('unmeasured document ownership')
    encoder=GraphEncoder(declarations_for(declarations,[{'objects':selected}]))
    copies=deepcopy(selected);byname={o['class_name']:o for o in copies};changes=[]
    storage=byname['ESSchemaStorage']['fields']
    if 'm_storedSchemas' not in storage or storage['m_dirty']!=0:raise ValueError('requires measured clean2024 schema storage')
    rows=storage['m_storedSchemas']
    own=uuid.UUID(SCHEMA_GUID).bytes_le
    def key(row):return bytes(row['first']['m_guid']['guid_bytes'])
    if [key(r)for r in rows]!=sorted(set(key(r)for r in rows)):raise ValueError('schema map not sorted unique')
    if own in [key(r)for r in rows]:raise ValueError('own schema already registered; migration/reattachment unsupported')
    rows.append({'first':guid(SCHEMA_GUID),'second':schema_definition()});rows.sort(key=key)
    tracking=byname['EStorageTracking']['fields']['m_trackingItems']
    tracking_keys=[bytes(r['m_schemaGuid']['m_guid']['guid_bytes'])for r in tracking]
    if tracking_keys!=sorted(set(tracking_keys)) or own in tracking_keys:raise ValueError('invalid/duplicate ES tracking schema')
    tracking.append({'m_schemaGuid':guid(SCHEMA_GUID),'m_elemIdSet':[identifier(owner_id)]})
    tracking.sort(key=lambda r:bytes(r['m_schemaGuid']['m_guid']['guid_bytes']))
    maps=byname['ElemsSetWithCellsTracking']['fields']['m_elemIdSetMap']
    keys=[r['first']for r in maps]
    if keys!=sorted(set(keys)):raise ValueError('cell tracker map not sorted unique')
    if any(owner_id==v['m_id']['m_id64']for r in maps for v in r['second']['m_idSet']):raise ValueError('owner already registered')
    matches=[r for r in maps if r['first']==-100]
    if not matches:maps.append({'first':-100,'second':{'m_idSet':[]}});maps.sort(key=lambda r:r['first']);matches=[r for r in maps if r['first']==-100]
    values=matches[0]['second']['m_idSet']
    ids=[v['m_id']['m_id64']for v in values]
    if ids!=sorted(set(ids)):raise ValueError('existing owner set not sorted unique')
    values.append(identifier(owner_id));values.sort(key=lambda v:v['m_id']['m_id64'])
    patches=[]
    for before,after in zip(selected,copies):
        start,end=before['start'],before['fields_end']
        if not 0<=start<end<=len(raw) or encoder.fields(before['class_tag'],before['fields'])!=raw[start:end]:
            raise ValueError('registration object source reconstruction differs')
        encoded=encoder.fields(after['class_tag'],after['fields']);patches.append((start,end,encoded))
        changes.append({'class_name':before['class_name'],'start':start,'end':end,'new_bytes':len(encoded)})
    patches.sort()
    if any(a[1]>b[0]for a,b in zip(patches,patches[1:])):raise ValueError('overlapping registration objects')
    result=raw
    for start,end,value in reversed(patches):result=result[:start]+value+result[end:]
    expected=deepcopy(graph)
    for o in expected['objects']:
        if o['class_name']in byname:o['fields']=byname[o['class_name']]['fields']
    return result,expected,changes


def metadata_values(application_id,name,properties):
    if not isinstance(application_id,str) or not application_id or not isinstance(name,str):raise ValueError('application ID and name must be strings; ID nonempty')
    if not isinstance(properties,dict) or any(not isinstance(k,str)for k in properties):raise ValueError('properties must be a JSON object with string keys')
    try:encoded=json.dumps(properties,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    except (ValueError,TypeError)as error:raise ValueError('properties must be finite JSON values')from error
    # Reject type coercion (tuples, non-string nested keys) that loses JSON types.
    if json.loads(encoded)!=properties:raise ValueError('properties do not roundtrip losslessly as JSON')
    values=(application_id,name,encoded)
    if any('\0'in v or len(v.encode('utf-16-le'))>2_000_000 for v in values):raise ValueError('invalid/oversized metadata string')
    return values


def owner_bodies(declarations,owner_id,application_id,name,properties):
    """Fresh DataStorage with only OUR entity; no vendor schemas are referenced."""
    if type(owner_id)is not int or not 0<owner_id<2**31:raise ValueError('bounded fresh owner ID required')
    values=metadata_values(application_id,name,properties);e=Encoder(declarations)
    if (e.tag('DataStorage'),e.tag('ElementHeader'),e.tag('SerializedDummy'))!=(1133,1439,3712):raise ValueError('only measured2024 native classes supported')
    root={k:{'token':0}for k in ('m_pParamValueSetDouble','m_pParamValueSetInt','m_pParamValueSetAString','m_pParamValueSetElementId','m_geomSteps','m_pGeomTable')}
    root.update(m_constrInfo=[],m_cellList=pointer('CellList'),m_docAccess={'m_pDoc':{'token':1}},m_id=identifier(owner_id),m_locked=False,m_moribund=False,m_dummy=False,m_name=name)
    for k in ('m_assocLevelId','m_famId','m_unplacedOwnerId','m_ownerDBViewId','m_createdPhaseId','m_demolishedPhaseId','m_designOptionId'):root[k]=identifier(-1)
    cells={'m_cells':[pointer('ESEntityCell')]}
    entities={'m_entityMap':[{'first':{'m_guid':SCHEMA_GUID},'second':{'m_blob':{'token':0xffffffff,'schema_guid':SCHEMA_GUID}}}]}
    body=struct.pack('<H',e.tag('DataStorage'))+e.fields(e.tag('DataStorage'),root)+e.fields(e.tag('CellList'),cells)+e.fields(e.tag('ESEntityCell'),entities)
    for value in values:
        raw=value.encode('utf-16-le');body+=struct.pack('<I',len(raw)//2)+raw
    header={'m_regenHistory':{'m_historyMap':[]},'m_viewRules':{'m_nVisibleViewFlags':-4225},'m_abFlags4Bytes':8206,'m_classDef':{'m_ref':'DataStorage'},'m_pBBox':{'token':0},'m_parents':pointer('ElementParents')}
    for k in ('m_categroryId','m_familyId','m_ownerViewId','m_designOptionId','m_unplacedOwnerId','m_miscId'):header[k]=identifier(-1)
    parents={k:[]for k in ('m_regenOnly','m_regenWildcards','m_nonDetermRegenChildren','m_dependencyParents','m_appearanceParents','m_deferredParents','m_deferredPropagationParents','m_computedParametersParents')}
    parents.update(m_deletion=[identifier(owner_id)],m_hasNonDetermRegenChildren=False)
    head=struct.pack('<H',e.tag('ElementHeader'))+e.fields(e.tag('ElementHeader'),header)+e.fields(e.tag('ElementParents'),parents)
    return {101:head,102:body,103:struct.pack('<H',e.tag('SerializedDummy'))+e.fields(e.tag('SerializedDummy'),{})}
