"""Independent saved generic-mesh document audit; no authoring imports.

Compares oriented rendered triangle multisets to explicit SI requests after
native float32 quantization. Native level association is deliberately distinct
from the application relationship stored in our extensible-storage payload.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import uuid
import zlib

SOURCE_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'
SCHEMA_GUID='3e6dd92d-a1e2-5529-bf69-045c18c5f87b'
SCHEMA_NAME='MovingAtomsElementPropertiesV1'
APP_GUID='b8620789-7098-5242-b12f-70f99c0517e4'
FIELDS=('ApplicationId','Name','PropertiesJson')
OPTIONS={'m_PresentationType':0,'m_ReferencingOption':0,'m_RoomBoundingOption':0,'m_AllowsChangeTypeId':False,'m_AllowsCopy':True,'m_AllowsLock':False,'m_AllowsMove':True,'m_AllowsTagAlongCurve':False}
ALIASES={'slab':'Floor','beam':'StructuralFraming','generic':'GenericModel','genericmodels':'GenericModel','genericmodel':'GenericModel','stairs':'Stair','walls':'Wall','slabs':'Floor','doors':'Door','windows':'Window','floors':'Floor','columns':'Column','beams':'StructuralFraming','pipes':'Pipe','ducts':'Duct','roofs':'Roof'}


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def eid(ident):return {'m_id':{'m_id64':ident}}
def guid(value):return {'m_guid':{'guid_bytes':list(uuid.UUID(value).bytes_le)}}
def sha(data):return hashlib.sha256(data).hexdigest()


def semantic(graph):
    def fields(v):
        if isinstance(v,list):return [fields(x)for x in v]
        if isinstance(v,dict):return {k:fields(x)for k,x in v.items()if not(k=='offset'and('pointer_token'in v or 'discriminator'in v))}
        return v
    return {'objects':[{'class_name':o['class_name'],'class_tag':o['class_tag'],'token':o['token'],'fields':fields(o['fields'])}for o in graph['objects']],
            'edges':[{k:v for k,v in e.items()if k!='pointer_offset'}for e in graph['edges']]}


def schema_definition():
    zero=guid('00000000-0000-0000-0000-000000000000')
    return {'m_guid':guid(SCHEMA_GUID),'m_schemaName':SCHEMA_NAME,'m_documentation':'Moving Atoms external element identity and JSON application properties, version 1',
            'm_readAccessLevel':1,'m_writeAccessLevel':1,'m_vendorId':'','m_applicationGUID':zero,
            'm_fields':[{'m_entryIndex':i,'m_fieldName':name,'m_fieldTypeName':'TCHAR','m_containerType':0,'m_documentation':'','m_specTypeId':{'m_typeId':''},'m_subSchemaGUID':zero}for i,name in enumerate(FIELDS)]}


def request_oracle(request):
    if not isinstance(request,dict)or set(request)!={'schema_version','units','levels','elements'}or type(request['schema_version'])is not int or request['schema_version']!=1 or request['units']!='metres':raise ValueError('schema1 explicit metres required')
    def label(v):
        if not isinstance(v,str)or not v or v!=v.strip()or '\0'in v or len(v)>128:raise ValueError('trimmed Unicode label required')
        try:v.encode('utf-16le')
        except UnicodeEncodeError as e:raise ValueError('invalid Unicode')from e
        return v
    def number(v,limit):
        if type(v)not in(int,float)or not math.isfinite(v)or abs(v)>limit:raise ValueError('finite bounded coordinate required')
        return float(v)
    def properties(v):
        if v is None or type(v)in(bool,int):return
        if type(v)is float:number(v,1e300);return
        if isinstance(v,str):
            if '\0'in v:raise ValueError('NUL property')
            v.encode('utf-16le');return
        if isinstance(v,list):
            for x in v:properties(x)
            return
        if isinstance(v,dict):
            for k,x in v.items():
                if not isinstance(k,str):raise ValueError('JSON string keys required')
                properties(k);properties(x)
            return
        raise ValueError('JSON properties only')
    if not isinstance(request['levels'],list)or len(request['levels'])>100:raise ValueError('level budget exceeded')
    levels=[];names=set();level_ids=set();fresh=[];next_id=2746
    for level in request['levels']:
        if not isinstance(level,dict)or set(level)!={'id','name','elevation'}:raise ValueError('level fields differ')
        app=label(level['id']);name=label(level['name']);z=number(level['elevation'],1000)
        if app in level_ids or name.casefold()in names:raise ValueError('duplicate level identity/name')
        if name.casefold()=='level 1'and(name!='Level 1'or z!=0):raise ValueError('reserved scaffold name')
        reused=name=='Level 1';ident=1916 if reused else next_id
        if not reused:fresh.append(ident);next_id+=1
        levels.append({'id':app,'name':name,'elevation_m':z,'element_id':ident,'reused_seed':reused});names.add(name.casefold());level_ids.add(app)
    bylevel={l['id']:l for l in levels}
    if not isinstance(request['elements'],list)or not 1<=len(request['elements'])<=100:raise ValueError('element budget exceeded')
    elements=[];ids=set();vertex_count=triangle_count=0
    for element in request['elements']:
        if not isinstance(element,dict)or not {'id','name','category','properties','parts'}<=set(element)or set(element)-{'id','name','category','properties','parts','level_id'}:raise ValueError('element fields differ')
        app=label(element['id']);name=label(element['name']);category=label(element['category'])
        if app in ids:raise ValueError('duplicate application element ID')
        ids.add(app);level_id=element.get('level_id')
        if 'level_id'in element and(not isinstance(level_id,str)or level_id not in bylevel):raise ValueError('unknown application level')
        props=element['properties']
        if not isinstance(props,dict):raise ValueError('properties object required')
        try:properties(props);encoded=canonical(props).encode('utf-16le')
        except(UnicodeEncodeError,RecursionError)as error:raise ValueError('invalid properties')from error
        if len(encoded)>1000000:raise ValueError('metadata budget exceeded')
        if not isinstance(element['parts'],list)or not 1<=len(element['parts'])<=100:raise ValueError('part budget exceeded')
        for part in element['parts']:
            if not isinstance(part,dict)or set(part)!={'vertices','triangles'}:raise ValueError('part fields differ')
            points=part['vertices'];faces=part['triangles']
            if not isinstance(points,list)or not points or not isinstance(faces,list)or not faces:raise ValueError('nonempty part arrays required')
            vertex_count+=len(points);triangle_count+=len(faces)
            for point in points:
                if not isinstance(point,list)or len(point)!=3:raise ValueError('XYZ required')
                for value in point:number(value,10000)
            for tri in faces:
                if not isinstance(tri,list)or len(tri)!=3 or any(type(i)is not int or not 0<=i<len(points)for i in tri):raise ValueError('invalid triangle indices')
        level=bylevel.get(level_id)
        metadata={'application_properties':props,'level':None if level is None else {'id':level['id'],'name':level['name'],'elevation_m':level['elevation_m'],'native_element_id':level['element_id']},'category':category}
        elements.append({'id':app,'name':name,'category':category,'element_id':next_id,'level_id':level_id,'metadata_properties':metadata,'request':element});next_id+=1
    if vertex_count>100000 or triangle_count>200000 or next_id-2746>100:raise ValueError('document budget exceeded')
    return {'levels':levels,'elements':elements,'new_level_ids':fresh,'new_element_ids':[e['element_id']for e in elements],'expected_new_ids':list(range(2746,next_id))}


def triangle_key(points):
    p=tuple(tuple(v)for v in points)
    return min(p,p[1:]+p[:1],p[2:]+p[:2])


def quantized(points):
    return [[struct.unpack('<f',struct.pack('<f',float(v)/.3048))[0]for v in point]for point in points]


def triangle_multiset(parts,*,metres=False):
    result=Counter()
    for part in parts:
        points=quantized(part['vertices'])if metres else part['vertices']
        for p in points:
            if len(p)!=3 or any(type(v)not in(int,float)or not math.isfinite(v)for v in p):raise ValueError('nonfinite triangle geometry')
        for face in part['triangles']:
            if len(face)!=3 or any(type(i)is not int or not 0<=i<len(points)for i in face):raise ValueError('invalid actual triangle indices')
            result[triangle_key([points[i]for i in face])]+=1
    return result


def category_context(category,profile):
    normalized=category.strip().lower().replace('_','').replace(' ','');byname={k.lower():k for k in profile['kinds']}
    selected=ALIASES.get(normalized,byname.get(normalized))
    if selected is None or not profile['kinds'][selected]['available']:raise ValueError('unqualified requested category')
    item=profile['kinds'][selected];styles={s['id']:s for s in profile['styles']};style=styles[item['projection_style_id']]
    if style['category_id']!=item['category_id']or style['style_kind']!=1 or style['owner_id']!=-1 or not style['material_resolved']:raise ValueError('unqualified projection style')
    return {'category_id':item['category_id'],'style_id':style['id'],'interior_style_id':style['id'],'material_id':style['material_id'],'canonical_category':selected}


def global_check(before,after,level_ids,owners):
    expected=semantic(before)
    def obj(name):
        found=[o['fields']for o in expected['objects']if o['class_name']==name]
        if len(found)!=1:raise ValueError('ambiguous Global object '+name)
        return found[0]
    datum=obj('DatumTracking');categories=obj('ElementTrackingData');levelrows=[r for r in categories['m_elems']if r['m_categoryId']==eid(-2000240)]
    if datum['m_elemIdSet']!=[eid(1916)]or len(levelrows)!=1 or levelrows[0]['m_elemIdSet']!=[eid(1916)]:raise ValueError('seed level registration differs')
    datum['m_elemIdSet']=[eid(i)for i in sorted([1916,*level_ids])];levelrows[0]['m_elemIdSet']=[eid(i)for i in sorted([1916,*level_ids])]
    storage=obj('ESSchemaStorage')
    if storage['m_dirty']!=0 or storage['m_storedSchemas']:raise ValueError('seed schema catalog not empty')
    storage['m_storedSchemas']=[{'first':guid(SCHEMA_GUID),'second':schema_definition()}]
    tracking=obj('EStorageTracking')
    if tracking['m_trackingItems']:raise ValueError('seed ES tracking not empty')
    tracking['m_trackingItems']=[{'m_schemaGuid':guid(SCHEMA_GUID),'m_elemIdSet':[eid(i)for i in sorted(owners)]}]
    cells=obj('ElemsSetWithCellsTracking')['m_elemIdSetMap'];matches=[r for r in cells if r['first']==-100]
    if len(matches)>1:raise ValueError('ambiguous generic cell tracker')
    if not matches:cells.append({'first':-100,'second':{'m_idSet':[]}});cells.sort(key=lambda r:r['first']);matches=[r for r in cells if r['first']==-100]
    old=[v['m_id']['m_id64']for v in matches[0]['second']['m_idSet']]
    if set(old)&set(owners):raise ValueError('new owner already registered')
    matches[0]['second']['m_idSet']=[eid(i)for i in sorted(old+owners)]
    if semantic(after)!=expected:raise ValueError('Global changed outside intended level and own-ES registrations')
    return {'fresh_levels':level_ids,'own_schema_owner_ids':owners,'all_other_global_semantics_preserved':True,'native_DirectShape_registration_policy':'no structural/category instance additions; hypothesis'}


def references(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k=='m_id64'and type(v)is int and v>0:yield v
            else:yield from references(v)
    elif isinstance(value,list):
        for v in value:yield from references(v)


def verify_element(actual,element,context,all_ids):
    ident=element['element_id'];records={r['channel']:r for r in actual['records']}
    if len(actual['records'])!=3 or set(records)!={101,102,103}:raise ValueError('incomplete new element channel inventory')
    if actual['summary']['current_records_outside_route']or actual['summary']['unsupported_graph_records']:raise ValueError('incomplete/off-route native records')
    catalog=actual['summary']['extensible_storage_catalog']['schemas']
    if set(catalog)!={SCHEMA_GUID}or catalog[SCHEMA_GUID]['raw_metadata']!=schema_definition():raise ValueError('dynamic own schema definition differs')
    positives=set()
    for r in records.values():
        if r['identity']['element_id']!=ident or r['source']['stream']!='Partitions/1'or not r['graph']or r['graph']['consumed_bytes']!=r['source']['body_bytes']:raise ValueError('new native identity/route/graph differs')
        positives.update(references([o['fields']for o in r['graph']['objects']]))
    if not positives<=all_ids:raise ValueError('dangling native element reference')
    root=records[102]['graph']['objects'][0]
    if root['class_name']!='DirectShape'or root['fields']['m_id']!=eid(ident)or root['fields']['m_assocLevelId']!=eid(-1)or root['fields']['m_options']!=OPTIONS:raise ValueError('DirectShape root identity/options/native association differs')
    data=[o['fields']for o in records[102]['graph']['objects']if o['class_name']=='DirectShapeDataCell']
    if data!=[{'m_appGUID':APP_GUID,'m_appDataGUID':element['id'],'m_name':element['name'],'m_categoryId':eid(context['category_id'])}]:raise ValueError('native application ID/name/category differs')
    entities=[o['fields']for o in records[102]['graph']['objects']if o['class_name']=='ExtensibleStorageEntity']
    if len(entities)!=1 or entities[0]['schema_guid']!=SCHEMA_GUID or entities[0]['schema_name']!=SCHEMA_NAME:raise ValueError('owned metadata entity absent/ambiguous')
    values=[f['raw_value']for f in entities[0]['fields']]
    if values[:2]!=[element['id'],element['name']]or len(values)!=3 or canonical(json.loads(values[2]))!=canonical(element['metadata_properties']):raise ValueError('application metadata lost or changed')
    expected=triangle_multiset(element['request']['parts'],metres=True)
    used_points=[p for tri in expected for p in tri];bounds=[[min(p[i]for p in used_points)for i in range(3)],[max(p[i]for p in used_points)for i in range(3)]]
    header=records[101]['graph']['objects'];outlines=[o['fields']['m_minmax']for o in header if o['class_name']=='Outline']
    if outlines!=[bounds]or header[0]['fields']['m_categroryId']!=eid(context['category_id']):raise ValueError('header bounds/category differ')
    for ch in(102,103):
        objects=records[ch]['graph']['objects'];roots=[o['fields']for o in objects if o['class_name']=='GElement'];topologies=[{'vertices':o['fields']['m_pointsArr'],'triangles':o['fields']['m_facetsArr']}for o in objects if o['class_name']=='FacetedTopology0']
        if len(roots)!=1 or roots[0]['m_elementId']!=ident or roots[0]['m_bBox']!=bounds or roots[0]['m_tightbBox']!=bounds or roots[0]['m_GInfo']['m_categoryId']!=eid(context['style_id']):raise ValueError('shape/display ownership/bounds/style differs')
        if triangle_multiset(topologies)!=expected:raise ValueError('native shape/display triangles differ from request')
        meshes=[o['fields']for o in objects if o['class_name']=='GPolyMesh']
        if not meshes or any(m['m_interiorGStyleID']!=eid(context['interior_style_id'])or m['m_materialID']!=eid(context['material_id'])for m in meshes):raise ValueError('mesh material/style differs')
    scene=actual['scene']
    if scene['units']!='feet'or scene['coordinate_frame']!='document Z-up'or any(s['current_records_outside_route']for s in scene['summaries']):raise ValueError('scene units/routes differ')
    if len(scene['elements'])!=1 or scene['elements'][0]['id']!=ident:raise ValueError('saved-scene owner differs')
    owner=scene['elements'][0];meshes=owner['meshes']
    if owner['status']!='decoded_saved_graphics'or owner['unresolved_material_primitives']or owner['referenced_graph_sources']:raise ValueError('partial or shared saved graphics')
    for key in('diagnostics','unbounded_faces','empty_trim_faces','rejected_filters','excluded_visibility_branches','excluded_non_surface_branches'):
        if meshes[key]:raise ValueError('saved graphics omitted geometry: '+key)
    if triangle_multiset(meshes['primitives'])!=expected:raise ValueError('oriented rendered triangle multiset differs from float32 SI request')
    for primitive in meshes['primitives']:
        if primitive['source_owner_id']is not None or len(primitive['normals'])!=len(primitive['vertices']):raise ValueError('shared/partial rendered primitive')
        if any(len(n)!=3 or not all(math.isfinite(v)for v in n)or abs(sum(v*v for v in n)-1)>1e-6 for n in primitive['normals']):raise ValueError('invalid rendered normals')
        for face in primitive['triangles']:
            a,b,c=[primitive['vertices'][i]for i in face];u=[b[i]-a[i]for i in range(3)];v=[c[i]-a[i]for i in range(3)]
            normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in normal))
            if length==0:raise ValueError('rendered triangle collapsed')
            normal=[x/length for x in normal]
            if any(sum(normal[j]*primitive['normals'][i][j]for j in range(3))<1-1e-6 for i in face):raise ValueError('rendered normal disagrees with oriented face')
        if primitive['render_style_id']!=context['interior_style_id']or primitive['material_id']!=(context['material_id']if context['material_id']>0 else None):raise ValueError('rendered primitive material/style differs')
    if set(owner['render_materials'])!={str(i)for i in range(len(meshes['primitives']))}:raise ValueError('render material coverage differs')
    for material in owner['render_materials'].values():
        if material['material_id']!=(context['material_id']if context['material_id']>0 else None)or material['diagnostics']:raise ValueError('render material identity unresolved or different')

    return {'element_id':ident,'application_id':element['id'],'name':element['name'],'category':element['category'],'category_context':context,'native_associated_level_id':-1,
            'application_level_relationship':element['metadata_properties']['level'],'application_properties_exact':True,'metadata_properties':element['metadata_properties'],
            'oriented_triangles_exact_after_SI_to_feet_float32':True,'triangle_count':sum(expected.values()),'rendered_primitive_count':len(meshes['primitives']),
            'positive_references_resolve':sorted(positives),'bounds_feet':bounds,'render_materials':owner['render_materials'],'meshes':meshes['primitives'],
            'channels':{str(ch):{'bytes':r['source']['body_bytes'],'sha256':r['source']['body_sha256'],'objects':len(r['graph']['objects'])}for ch,r in records.items()}}


def verify_level(actual,source_graphs,level,all_ids):
    ident=level['element_id'];records={r['channel']:r for r in actual['records']}
    if len(records)!=3 or actual['summary']['current_records_outside_route']:raise ValueError('saved level route incomplete')
    for ch,r in records.items():
        g=r['graph'];stream='Partitions/0'if level['reused_seed']else'Partitions/1'
        if not g or g['consumed_bytes']!=r['source']['body_bytes']or r['source']['stream']!=stream:raise ValueError('saved level body incomplete')
        if not set(references([o['fields']for o in g['objects']]))<=all_ids:raise ValueError('dangling level reference')
        expected=semantic(source_graphs[ch]);z=level['elevation_m']/.3048
        if ch==101:
            parents=next(o for o in expected['objects']if o['class_name']=='ElementParents')['fields']['m_deletion']
            if parents!=[eid(1910),eid(1916)]:raise ValueError('source level parents differ')
            parents[1]=eid(ident)
        if ch==102:
            zs=[o['fields']['m_origin'][2]for o in g['objects']if o['class_name']=='Plane']
            if len(zs)!=2 or zs[0]!=zs[1]or abs(zs[0]-z)>1e-9:raise ValueError('native level elevation differs')
            expected['objects'][0]['fields']['m_id']=eid(ident);expected['objects'][0]['fields']['m_text']=level['name']
            for obj in expected['objects']:
                if obj['class_name']=='Plane':obj['fields']['m_origin'][2]=zs[0]
        if semantic(g)!=expected:raise ValueError('level changed beyond identity/name/elevation')
    return {**level,'complete_saved_graphs_match':True}


def expected_probe_sources():
    here=Path(__file__).parent
    sources={'index':(here/'wall_candidate_probe.rs').read_bytes(),'scene':(here/'seed_directshape_probe.rs').read_bytes()}
    needle=b'channels: [101, 102, 103].into_iter().collect(),'
    if sources['scene'].count(needle)!=1:raise ValueError('saved-scene probe profile changed')
    sources['scene']=sources['scene'].replace(needle,needle+b'\n        max_graph_values: 10_000_000,')
    return sources


def validated_prebuilt_probes(config,sources,revision):
    if set(config)!={'index','scene','reader_revision','source_sha256','binary_sha256'}or config['reader_revision']!=revision:raise ValueError('prebuilt probe provenance differs')
    paths={}
    for name,source in sources.items():
        path=Path(config[name]).resolve()
        if config['source_sha256'].get(name)!=sha(source)or config['binary_sha256'].get(name)!=sha(path.read_bytes()):raise ValueError('prebuilt probe hash differs')
        paths[name]=path
    return paths


def verify(reader,target,source,candidate,plan,request,*,prebuilt_probes=None):
    import olefile
    from codec import decode as unpage
    from wall_batch_metadata_audit import audit_table,audit_history,inflate_global
    from schema_probe import REV
    oracle=request_oracle(request)
    if request_oracle(plan['request'])!=oracle:raise ValueError('plan and independent request differ')
    reader=reader.resolve()if reader is not None else None;target=target.resolve();source=source.resolve();candidate=candidate.resolve();here=Path(__file__).parent
    if sha(source.read_bytes())!=SOURCE_SHA or plan['source_sha256']!=SOURCE_SHA:raise ValueError('source seed differs')
    if prebuilt_probes is None:
        if reader is None:raise ValueError('reader source required without prebuilt probes')
        if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
        subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    category_bytes=(here/'results/seed_categories.json').read_bytes();categories=json.loads(category_bytes)
    if categories['seed_sha256']!=SOURCE_SHA or categories['reader_revision']!=REV:raise ValueError('category evidence provenance differs')
    with tempfile.TemporaryDirectory(dir=candidate.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir()
        sources=expected_probe_sources()
        if prebuilt_probes is None:
            manifest='[package]\nname="rvt-seed-model-verifier"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n'
            for name,data in sources.items():
                (work/'src'/f'{name}.rs').write_bytes(data);manifest+=f'[[bin]]\nname="seed-model-{name}"\npath="src/{name}.rs"\n'
            (work/'Cargo.toml').write_text(manifest)
            subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
            probe_paths={name:target/'release'/('seed-model-'+name)for name in sources}
        else:probe_paths=validated_prebuilt_probes(prebuilt_probes,sources,REV)
        def probe(kind,*args):return json.loads(subprocess.check_output([str(probe_paths[kind]),*map(str,args)]))
        indexes=[];parts=[];raws=[];globals=[]
        for path in(source,candidate):
            with olefile.OleFileIO(path)as f:
                schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
                if sha(schema)!=plan['seed_schema_sha256']or sha(schema)!=categories['seed_schema_sha256']:raise ValueError('saved schema differs')
                (work/'schema.bin').write_bytes(schema)
                raw={n:inflate_global(f.openstream('Global/'+n).read())for n in('ElemTable','History','Latest')};raws.append(raw)
                (work/'table.bin').write_bytes(raw['ElemTable']);(work/'history.bin').write_bytes(raw['History'])
                indexes.append(probe('index','identity',work/'schema.bin',work/'table.bin',work/'history.bin')['identities'])
                if raw['Latest'][-4:]!=bytes(4):raise ValueError('unqualified Global footer')
                (work/'global.bin').write_bytes(raw['Latest'][:-4]);globals.append(probe('index','decode',work/'schema.bin',work/'global.bin')['graph'])
                parts.append({'/'.join(p):sha(f.openstream(p).read())for p in f.listdir()if p[0]=='Partitions'})
        history=audit_history(raws[0]['History'],raws[1]['History']);table=audit_table(raws[0]['ElemTable'],raws[1]['ElemTable'],history['creation_episode'])
        if table['new_ids']!=oracle['expected_new_ids']or table['new_ids']!=plan['expected_new_ids']or history['creation_episode']!=1 or history['new_episode_guid']!=plan['new_episode_guid']:raise ValueError('raw saved allocation/episode differs')
        old,new=indexes
        if set(new)!=set(old)|{str(i)for i in oracle['expected_new_ids']}or any(new[k]!=v for k,v in old.items()):raise ValueError('prior identities changed or unrequested elements')
        if len({v['unique_id']for v in new.values()})!=len(new):raise ValueError('duplicate native identity')
        if set(parts[1])!=set(parts[0])|{'Partitions/1'}or any(parts[1][k]!=v for k,v in parts[0].items()):raise ValueError('original partition altered')
        registration=global_check(*globals,oracle['new_level_ids'],oracle['new_element_ids'])
        actual_levels=[{k:l[k]for k in('id','name','elevation_m','element_id','reused_seed')}for l in plan['levels']]
        if actual_levels!=oracle['levels']or plan['new_level_ids']!=oracle['new_level_ids']or plan['new_element_ids']!=oracle['new_element_ids']:raise ValueError('application/native identity map differs')
        source_level=probe('index',source,1916);source_graphs={r['channel']:r['graph']for r in source_level['records']}
        if set(source_graphs)!={101,102,103}or not all(source_graphs.values()):raise ValueError('source scaffold incomplete')
        if source_graphs[102]['objects'][0]['fields']['m_text']!='Level 1'or [o['fields']['m_origin'][2]for o in source_graphs[102]['objects']if o['class_name']=='Plane']!=[0,0]:raise ValueError('source scaffold name/elevation differs')
        level_reports=[];evidence=[]
        for level in oracle['levels']:
            ident=level['element_id'];actual=probe('index',candidate,ident);records={r['channel']:r for r in actual['records']}
            if len(records)!=3 or actual['summary']['current_records_outside_route']:raise ValueError('saved level route incomplete')
            verify_level(actual,source_graphs,level,{int(i)for i in new})
            level_reports.append({**level,'native_identity':new[str(ident)],'complete_saved_graphs_match':True});evidence.append(actual)
        elements=[];context_reports=[];saved_materials={};style_records={}
        planned={e['element_id']:e for e in plan['elements']}
        if set(planned)!=set(oracle['new_element_ids']):raise ValueError('planned element inventory differs')
        for element in oracle['elements']:
            ident=element['element_id'];p=planned[ident]
            if any(p[k]!=element[k]for k in('id','name','level_id'))or canonical(p['metadata_properties'])!=canonical(element['metadata_properties']):raise ValueError('plan application metadata differs')
            context=category_context(element['category'],categories);style_id=context['style_id']
            if style_id not in style_records:
                actual_style=probe('index',candidate,style_id);record=next(r for r in actual_style['records']if r['channel']==102)
                root=record['graph']['objects'][0]
                if root['class_name']!='GStyleElem'or root['fields']['m_categoryId']!=eid(context['category_id'])or root['fields']['m_gstyleType']!=1 or record['source']['stream']!='Partitions/0':raise ValueError('saved style category/type differs')
                material_fields=[o['fields']['m_materialElemId']for o in record['graph']['objects']if 'm_materialElemId'in o['fields']]
                if material_fields!=[eid(context['material_id'])]:raise ValueError('saved style material differs')
                profile_style=next(s for s in categories['styles']if s['id']==style_id)
                if record['source']['body_sha256']!=profile_style['source']['body_sha256']:raise ValueError('category evidence not bound to actual saved style')
                style_records[style_id]=record;context_reports.append({'style_id':style_id,'body_sha256':record['source']['body_sha256'],**context})
            actual=probe('scene',candidate,ident)
            report=verify_element(actual,element,context,{int(i)for i in new})
            for record in actual['records']:
                if record['source']['body_sha256']!=p['body_sha256'][str(record['channel'])]:raise ValueError('plan/body hash differs')
            report['native_identity']=new[str(ident)];elements.append(report);evidence.append(actual)
        evidence_path=candidate.with_name(candidate.stem+'-independent-scene.json');evidence_path.write_text(json.dumps({'candidate_sha256':sha(candidate.read_bytes()),'records_and_scenes':evidence},indent=2,ensure_ascii=False)+'\n')
        return {'source_sha256':SOURCE_SHA,'candidate_sha256':sha(candidate.read_bytes()),'reader_revision':REV,'request':request,'table_audit':table,'history_audit':history,
            'prior_native_identities_preserved':len(old),'original_partitions_preserved':len(parts[0]),'global_registration':registration,'levels':level_reports,'elements':elements,
            'application_identity_map':{'levels':[{k:v for k,v in l.items()if k!='request'}for l in oracle['levels']],'elements':[{'application_id':e['id'],'native_element_id':e['element_id'],'native_unique_id':new[str(e['element_id'])]['unique_id']}for e in oracle['elements']]},
            'category_context':context_reports,'category_evidence_sha256':sha(category_bytes),'probe_sources_sha256':{k:sha(v)for k,v in sources.items()},'probe_binary_sha256':{k:sha(v.read_bytes())for k,v in probe_paths.items()},'native_probe_max_graph_values':10000000,
            'saved_evidence_path':str(evidence_path),'saved_evidence_sha256':sha(evidence_path.read_bytes()),'native_level_association_policy':'m_assocLevelId remains -1; requested relationship is own-schema metadata only',
            'ordinary_ifc_projection':'not used: pinned exporter does not map DirectShape','geometry_claim':'oriented saved/rendered surface triangles; no native solid or regeneration guarantee',
            'autodesk_acceptance':'not_tested','production_native_export':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader',type=Path,required=True);p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/seed-model-verify-build');p.add_argument('--source',type=Path,default=Path(__file__).parent/'local/minimal_seed-Project.rvt');p.add_argument('--candidate',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.reader,a.target,a.source,a.candidate,json.loads(a.plan.read_bytes()),json.loads(a.request.read_bytes()));a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
