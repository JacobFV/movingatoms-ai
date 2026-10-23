"""Independent saved minimal-seed transaction and physical-solid auditor.

Does not call candidate generation or reference-remapping encoders. Builder
plans specify requested solids; saved data and source records are authorities.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zlib

WIDTH=0.2/0.3048
SEED_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'


def request_oracle(request):
    """Independent SI request validation and deterministic identity allocation."""
    if not isinstance(request,dict)or set(request)!={'schema_version','units','levels','walls'}or request['schema_version']!=1 or type(request['schema_version'])is not int or request['units']!='metres':raise ValueError('explicit schema1 metre request required')
    def number(value):
        if type(value)not in(int,float)or not math.isfinite(value):raise ValueError('finite numeric value required')
        return float(value)
    def label(value):
        if not isinstance(value,str)or not value or value!=value.strip()or '\0'in value or len(value)>128:raise ValueError('trimmed Unicode label up to128 characters required')
        try:value.encode('utf-16le')
        except UnicodeEncodeError as error:raise ValueError('invalid Unicode label')from error
        return value
    if not isinstance(request['levels'],list)or not 1<=len(request['levels'])<=100 or not isinstance(request['walls'],list)or not 1<=len(request['walls'])<=100:raise ValueError('1..100 levels and walls required')
    levels={};fresh=[];next_id=2746
    for level in request['levels']:
        if not isinstance(level,dict)or set(level)!={'name','elevation'}:raise ValueError('level fields differ')
        name=label(level['name']);z=number(level['elevation'])
        if not -1000<=z<=1000:raise ValueError('level elevation outside qualified range')
        if not isinstance(name,str)or not name.strip()or '\0'in name or name.casefold()in {n.casefold()for n in levels}:raise ValueError('unique nonempty level names required')
        if name.casefold()=='level 1'and (name!='Level 1'or z!=0):raise ValueError('retained scaffold name requires exact zero-level reuse')
        reused=name=='Level 1'and z==0
        ident=1916 if reused else next_id
        if not reused:fresh.append(ident);next_id+=1
        levels[name]={'name':name,'elevation_m':z,'element_id':ident,'reused_seed':reused}
    walls=[];ids=set()
    for wall in request['walls']:
        if not isinstance(wall,dict)or not {'id','base_level','top_level','start','length','height'}<=set(wall)or set(wall)-{'id','base_level','top_level','start','length','height','yaw_degrees','thickness','kind'}:raise ValueError('wall fields differ')
        ident=label(wall['id'])
        if not isinstance(ident,str)or not ident.strip()or '\0'in ident or ident in ids:raise ValueError('unique application wall IDs required')
        ids.add(ident)
        if not isinstance(wall['base_level'],str)or not isinstance(wall['top_level'],str)or wall['base_level']not in levels or wall['top_level']not in levels:raise ValueError('wall level missing')
        base=levels[wall['base_level']];top=levels[wall['top_level']]
        if top['elevation_m']<=base['elevation_m']:raise ValueError('ordered level elevations required')
        if not isinstance(wall['start'],list)or len(wall['start'])!=2:raise ValueError('world XY pair required')
        start=[number(v)for v in wall['start']];length=number(wall['length']);height=number(wall['height']);yaw=number(wall.get('yaw_degrees',0));thickness=number(wall.get('thickness',.2))
        if not .01<=length<=1000 or not .01<=height<=1000 or not -360<=yaw<=360 or any(abs(v)>10000 for v in start)or thickness!=.2 or wall.get('kind','straight')!='straight':raise ValueError('only positive straight200mm walls qualified')
        normalized={'id':ident,'base_level':wall['base_level'],'top_level':wall['top_level'],'start':start,'length':length,'height':height,'yaw_degrees':yaw,'thickness':thickness,'kind':'straight'}
        walls.append({'id':ident,'element_id':next_id,'request':normalized,'base_level_id':base['element_id'],'top_level_id':top['element_id'],'base_elevation_m':base['elevation_m'],'top_elevation_m':top['elevation_m']});next_id+=1
    if next_id-2746>100:raise ValueError('at most100 newly allocated elements supported')
    return {'levels':list(levels.values()),'walls':walls,'new_level_ids':fresh,'new_wall_ids':[w['element_id']for w in walls],'expected_new_ids':list(range(2746,next_id))}


def vertices(spec):
    """Requested world-metre cuboid converted to native feet independently."""
    yaw=math.radians(spec['yaw_degrees']);c,s=math.cos(yaw),math.sin(yaw)
    return [[(spec['start'][0]+c*x-s*y)/.3048,(spec['start'][1]+s*x+c*y)/.3048,(spec['base_elevation_m']+z)/.3048]
            for x in(0,spec['length'])for y in(-.1,.1)for z in(0,spec['height'])]


def global_check(before,after,wall_ids,level_ids):
    from new_element_registration import semantic_graph
    expected=semantic_graph(before)
    def obj(name):
        values=[o['fields']for o in expected['objects']if o['class_name']==name]
        if len(values)!=1:raise ValueError('ambiguous Global tracking object')
        return values[0]
    def ids(values):return [{'m_id':{'m_id64':i}}for i in values]
    structural=obj('StructuralElemSetTracking');datum=obj('DatumTracking')
    if structural['m_elemIdSet']!=[] or datum['m_elemIdSet']!=ids([1916]):raise ValueError('unexpected source tracking')
    structural['m_elemIdSet']=ids(sorted(wall_ids));datum['m_elemIdSet']=ids(sorted([1916,*level_ids]))
    levels=[v for v in obj('ElementTrackingData')['m_elems']if v['m_categoryId']['m_id']['m_id64']==-2000240]
    if len(levels)!=1 or levels[0]['m_elemIdSet']!=ids([1916]):raise ValueError('unexpected source level category')
    levels[0]['m_elemIdSet']=ids(sorted([1916,*level_ids]))
    if semantic_graph(after)!=expected:raise ValueError('Global changed outside exactly three tracking lists')
    return {'changed_lists':3 if level_ids else 1,'wall_registration':wall_ids,'level_registration':level_ids,'all_other_global_semantics_unchanged':True,'plan_view_policy':'no new association; hypothesis'}


def wall_semantics(graph,ident,spec):
    root=graph['objects'][0]
    if root['class_name']!='SWall':raise ValueError('not SWall')
    f=root['fields'];height=spec['request']['height']/.3048
    expected={'m_id':ident,'m_WallAttributesId':1947,'m_assocLevelId':spec['base_level_id'],'m_upToLevelId':spec['top_level_id'],'m_createdPhaseId':4}
    for key,value in expected.items():
        if f[key]['m_id']['m_id64']!=value:raise ValueError('wall semantic reference differs '+key)
    if f['m_roomBounding']is not False:raise ValueError('unexpected room bounding')
    cells=[o for o in graph['objects']if o['class_name']=='AnalyticalSpaceBoundingCell']
    if len(cells)!=1 or cells[0]['fields']['m_isSpaceBounding']is not False:raise ValueError('unexpected space bounding')
    sets=[o for o in graph['objects']if o['class_name']=='ParamValueSetDouble']
    if len(sets)!=1:raise ValueError('ambiguous wall parameters')
    params={p['m_paramId']['m_id']['m_id64']:p['m_value']for p in sets[0]['fields']['m_paramSet']}
    top_offset=(spec['base_elevation_m']+spec['request']['height']-spec['top_elevation_m'])/.3048
    for key,value in {-1001108:0,-1001109:top_offset,-1001101:height}.items():
        if key not in params or not math.isclose(params[key],value,abs_tol=1e-9):raise ValueError('wall vertical constraint differs')
    return {'base_level':spec['base_level_id'],'upper_level':spec['top_level_id'],'base_elevation_metres':spec['base_elevation_m'],'upper_elevation_metres':spec['top_elevation_m'],'type':1947,'phase':4,'width_feet':WIDTH,'height_feet':height,'base_offset_feet':params[-1001108],'top_offset_feet':params[-1001109]}


def verify(reader,target,source,candidate,plan,request):
    import olefile
    from codec import decode as unpage
    from save_candidate import unpack_global
    from wall_batch_metadata_audit import audit_table,audit_history
    from schema_probe import REV
    from wall_batch_verify import near,vertex_set_matches
    from wall_brep_audit import audit_graph,face_polygon,resolver
    from new_element_experiment import references
    from new_element_registration import semantic_graph
    oracle=request_oracle(request)
    if request_oracle(plan['request'])!=oracle:raise ValueError('plan request differs from independently supplied request')
    reader=reader.resolve();target=target.resolve();source=source.resolve();candidate=candidate.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SEED_SHA or plan['source_sha256']!=SEED_SHA:raise ValueError('seed source differs')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=candidate.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir();probe_source=Path(__file__).with_name('wall_candidate_probe.rs').read_bytes();(work/'src/main.rs').write_bytes(probe_source)
        (work/'Cargo.toml').write_text('[package]\nname="rvt-seed-document-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-seed-document-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        indexes=[];parts=[];raws=[];globals=[]
        for path in(source,candidate):
            with olefile.OleFileIO(path)as file:
                schema=zlib.decompress(unpage(file.openstream('Formats/Latest').read()),31)
                if hashlib.sha256(schema).hexdigest()!=plan['seed_schema_sha256']:raise ValueError('schema changed')
                (work/'schema.bin').write_bytes(schema)
                raw={name:unpack_global(unpage(file.openstream('Global/'+name).read()))[0]for name in ('ElemTable','History','Latest')};raws.append(raw)
                (work/'table.bin').write_bytes(raw['ElemTable']);(work/'history.bin').write_bytes(raw['History'])
                indexes.append(probe('identity',work/'schema.bin',work/'table.bin',work/'history.bin')['identities'])
                parts.append({'/'.join(p):hashlib.sha256(file.openstream(p).read()).hexdigest()for p in file.listdir()if p[0]=='Partitions'})
                if raw['Latest'][-4:]!=bytes(4):raise ValueError('unqualified Global footer')
                (work/'global.bin').write_bytes(raw['Latest'][:-4]);globals.append(probe('decode',work/'schema.bin',work/'global.bin')['graph'])
        history=audit_history(raws[0]['History'],raws[1]['History']);table=audit_table(raws[0]['ElemTable'],raws[1]['ElemTable'],history['creation_episode'])
        level_ids=oracle['new_level_ids'];wall_ids=oracle['new_wall_ids'];expected_ids=oracle['expected_new_ids']
        if [{k:l[k]for k in('name','elevation_m','element_id','reused_seed')}for l in plan['levels']]!=oracle['levels'] or plan['new_wall_ids']!=wall_ids or plan['new_level_ids']!=level_ids:raise ValueError('application/native identity map differs')
        if table['new_ids']!=expected_ids or table['new_ids']!=plan['expected_new_ids'] or history['creation_episode']!=1:raise ValueError('new allocation differs')
        if history['new_episode_guid']!=plan['new_episode_guid']:raise ValueError('new episode differs')
        old,new=indexes
        if set(new)!=set(old)|{str(i)for i in expected_ids}or any(new[k]!=v for k,v in old.items()):raise ValueError('old identities changed')
        if len({v['unique_id']for v in new.values()})!=len(new):raise ValueError('duplicate native identity')
        if set(parts[1])!=set(parts[0])|{'Partitions/1'}or any(parts[1][k]!=v for k,v in parts[0].items()):raise ValueError('old partitions changed')
        registration=global_check(*globals,wall_ids,level_ids)
        context=[]
        for ident,cls in [(1910,'LevelAttributes'),(1916,'Level'),(1947,'BasicWallType'),(4,'ProjectPhase'),(91,'MaterialElem'),(119,'GStyleElem'),(125,'GStyleElem'),(796,'GStyleElem')]:
            result=probe(candidate,ident)
            record=next((r for r in result['records']if r['channel']==102),None)
            if result['summary']['current_records_outside_route']or not record or record['class_name']!=cls or not record['graph'] or record['source']['stream']!='Partitions/0':raise ValueError('saved seed context class/route differs '+str(ident))
            if ident==1947:
                widths=[]
                def collect(value):
                    if isinstance(value,dict):
                        if 'm_layerWidth'in value:widths.append(value['m_layerWidth'])
                        for v in value.values():collect(v)
                    elif isinstance(value,list):
                        for v in value:collect(v)
                collect([o['fields']for o in record['graph']['objects']])
                if len(widths)!=1 or not math.isclose(widths[0],WIDTH,abs_tol=1e-12):raise ValueError('actual seed type width differs')
            context.append({'id':ident,'class':cls,'body_sha256':record['source']['body_sha256']})
        seed_level_records=probe(source,1916)['records']
        seed_level_graphs={r['channel']:r['graph']for r in seed_level_records}
        if set(seed_level_graphs)!={101,102,103}or not all(seed_level_graphs.values()):raise ValueError('source scaffold level incomplete')
        sf=seed_level_graphs[102]['objects'][0]['fields']
        if sf['m_text']!='Level 1'or sf['m_attrId']['m_id']['m_id64']!=1910 or [o['fields']['m_origin'][2]for o in seed_level_graphs[102]['objects']if o['class_name']=='Plane']!=[0,0]:raise ValueError('source scaffold name/elevation/type differs')
        rows=[];all_records=[]
        requested={w['element_id']:w for w in plan['walls']}
        specs={w['element_id']:w for w in oracle['walls']}
        level_specs={l['element_id']:l for l in oracle['levels']}
        for ident,wall in requested.items():
            if ident not in specs or any(wall[k]!=specs[ident][k]for k in('id','base_level_id','top_level_id')):raise ValueError('wall application/native mapping differs')
        if set(requested)!=set(wall_ids):raise ValueError('wall request inventory differs')
        for ident in expected_ids:
            current=probe(candidate,ident)
            if current['summary']['current_records_outside_route']or len(current['records'])!=3:raise ValueError('new record route incomplete')
            records={r['channel']:r for r in current['records']}
            if set(records)!={101,102,103}:raise ValueError('channel inventory differs')
            channels={};refs=[]
            for ch,r in records.items():
                g=r['graph']
                if not g or g['consumed_bytes']!=r['source']['body_bytes']or r['source']['stream']!='Partitions/1':raise ValueError('incomplete graph or wrong route')
                expected_hash=(next(l['body_sha256']for l in plan['levels']if l['element_id']==ident)if ident in level_ids else requested[ident]['body_sha256'])[str(ch)]
                if r['source']['body_sha256']!=expected_hash:raise ValueError('plan body digest differs')
                channels[str(ch)]={'bytes':g['consumed_bytes'],'sha256':r['source']['body_sha256'],'objects':len(g['objects']),'edges':len(g['edges'])}
                refs.extend(ref['id']for o in g['objects']for ref in references(o['fields'])if ref['id']>0)
            if any(str(ref)not in new for ref in refs):raise ValueError('dangling positive element reference')
            row={'id':ident,'identity':new[str(ident)],'channels':channels,'positive_element_references':sorted(set(refs))}
            if ident in level_ids:
                level=records[102]['graph']['objects'][0]
                if level['class_name']!='Level'or level['fields']['m_id']['m_id']['m_id64']!=ident or level['fields']['m_text']!=level_specs[ident]['name']or level['fields']['m_attrId']['m_id']['m_id64']!=1910:raise ValueError('level name/type differs')
                zs=[o['fields']['m_origin'][2]for o in records[102]['graph']['objects']if o['class_name']=='Plane']
                elevation=level_specs[ident]['elevation_m']/.3048
                if len(zs)!=2 or zs[0]!=zs[1] or any(not math.isclose(z,elevation,abs_tol=1e-9)for z in zs):raise ValueError('level elevation differs')
                row.update(name=level_specs[ident]['name'],elevation_feet=elevation,elevation_metres=level_specs[ident]['elevation_m'])
                for ch,source_graph in seed_level_graphs.items():
                    expected=semantic_graph(source_graph)
                    if ch==101:
                        parents=[o for o in expected['objects']if o['class_name']=='ElementParents']
                        if len(parents)!=1:raise ValueError('ambiguous source level parents')
                        deletion=parents[0]['fields']['m_deletion']
                        if [x['m_id']['m_id64']for x in deletion]!=[1910,1916]:raise ValueError('unexpected seed level deletion dependencies')
                        deletion[1]['m_id']['m_id64']=ident
                    if ch==102:
                        expected['objects'][0]['fields']['m_id']['m_id']['m_id64']=ident
                        expected['objects'][0]['fields']['m_text']=level_specs[ident]['name']
                        for obj in expected['objects']:
                            if obj['class_name']=='Plane':obj['fields']['m_origin'][2]=zs[0]
                    if semantic_graph(records[ch]['graph'])!=expected:raise ValueError('new level changed outside identity/name/plane elevation')

            else:
                wall=specs[ident];spec={**wall['request'],'base_elevation_m':wall['base_elevation_m']};height=spec['height']/.3048;row['spec']=spec;row['application_id']=wall['id']
                row['constraints']=wall_semantics(records[102]['graph'],ident,wall)
                allowed={ident,4,91,119,125,796,1947,wall['base_level_id'],wall['top_level_id']}
                if set(refs)!=allowed:raise ValueError('wall context inventory differs')
                geometry_root=records[103]['graph']['objects'][0]
                if geometry_root['class_name']!='GElement'or geometry_root['fields']['m_elementId']!=ident or geometry_root['fields']['m_GInfo']['m_tag']!=ident:raise ValueError('saved geometry owner differs')
                brep=audit_graph(records[103]['graph']);closed=[s for s in brep['geometry_components']if s['closed']]
                if len(closed)!=1:raise ValueError('expected exactly one closed solid')
                points=[];resolve=resolver(records[103]['graph'])
                for face in closed[0]['face_loops']:
                    polygon,_,_=face_polygon(records[103]['graph'],face['face_object'],resolve)
                    for point in polygon:
                        if not any(near(point,p)for p in points):points.append(point)
                if not vertex_set_matches(points,vertices(spec),1e-7):raise ValueError('native vertices differ from independent requested cuboid')
                length=spec['length']/.3048;volume=length*WIDTH*height;area=2*(length*WIDTH+length*height+WIDTH*height)
                if not math.isclose(brep['closed_solid_volume_cubic_feet'],volume,abs_tol=1e-7)or not math.isclose(closed[0]['surface_area_square_feet'],area,abs_tol=1e-7):raise ValueError('native volume/surface differs')
                bounds=brep['native_vertex_bounds_feet'];outlines=[o['fields']['m_minmax']for o in records[101]['graph']['objects']if o['class_name']=='Outline']
                if len(outlines)!=1 or not all(near(a,b)for a,b in zip(outlines[0],bounds)):raise ValueError('header bounds differ')
                row.update(native_brep=brep,native_vertices_feet=points,independent_requested_vertices_match=True,header_bounds_match=True)
            rows.append(row);all_records.extend(current['records'])
        # Public exporter output is an additional independent projection, not a
        # substitute for actual native solid checks above.
        projections=[];artifacts=[]
        for label,path in [('source',source),('candidate',candidate)]:
            outfile=work/(label+'.ifc');projection=probe('projection',path,outfile);data=outfile.read_bytes();artifact=candidate.with_name(candidate.stem+'-'+label+'.ifc')
            if artifact.exists()and artifact.read_bytes()!=data:raise ValueError('existing STEP artifact differs')
            if not artifact.exists():artifact.write_bytes(data)
            projections.append(projection);artifacts.append({'path':str(artifact),'sha256':hashlib.sha256(data).hexdigest()})
        before,after=projections
        if before['entities']:raise ValueError('seed unexpectedly projects physical elements')
        projected={e['type_guid']:e for e in after['entities']}
        if set(projected)!={str(i)for i in wall_ids}:raise ValueError('projected candidate contains missing/extraneous physical elements')
        for row in rows:
            if row['id']in wall_ids:row['ifc_projection']=projected[str(row['id'])];row['ifc_guid']=after['native_ids'][str(row['id'])]
        graphfile=candidate.with_name(candidate.stem+'-independent-graphs.json');graphfile.write_text(json.dumps({'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'records':all_records},indent=2)+'\n')
        return {'source_sha256':SEED_SHA,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'reader_revision':REV,
                'table_audit':table,'history_audit':history,'prior_identities_preserved':len(old),'original_partitions_preserved':len(parts[0]),'global_registration':registration,
                'request':request,'application_identity_map':oracle,'scaffold_level1916_preserved':True,'context':context,'records':rows,'ifc_artifacts':artifacts,'only_requested_physical_elements_projected':True,'independent_graphs_path':str(graphfile),'independent_graphs_sha256':hashlib.sha256(graphfile.read_bytes()).hexdigest(),
                'probe_source_sha256':hashlib.sha256(probe_source).hexdigest(),'probe_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'autodesk_acceptance':'not_tested','production_native_export':False}

def ifc_verify(report):
    """Isolated IfcOpenShell/OpenCASCADE STEP schema and world-mesh oracle."""
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    import ifcopenshell.validate
    import numpy as np
    from wall_candidate_ifc_owner_control import correct
    from wall_batch_verify import vertex_set_matches
    models=[];schemas=[];controls=[];artifacts=[]
    for artifact in report['ifc_artifacts']:
        path=Path(artifact['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=artifact['sha256']:raise ValueError('STEP artifact changed')
        original=ifcopenshell.open(str(path));logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(original,logger,express_rules=True)
        raw_messages=[{'level':x.get('level'),'message':x.get('message'),'instance':str(x.get('instance'))}for x in logger.statements]
        corrected=path.with_name(path.stem+'-owner-corrected.ifc');control=correct(path,corrected)
        model=ifcopenshell.open(str(corrected));logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(model,logger,express_rules=True)
        if logger.statements:raise ValueError('corrected IFC has schema errors')
        models.append(model);controls.append(control);schemas.append({'raw_messages':raw_messages,'corrected_messages':[]});artifacts.append({'path':str(corrected),'sha256':hashlib.sha256(corrected.read_bytes()).hexdigest()})
    if models[0].by_type('IfcWall'):raise ValueError('source contains wall meshes')
    scale=ifcopenshell.util.unit.calculate_unit_scale(models[1])
    storeys=models[1].by_type('IfcBuildingStorey');byname={s.Name:s for s in storeys}
    if len(byname)!=len(storeys):raise ValueError('duplicate IFC storey name')
    expected_levels=report['application_identity_map']['levels']
    for level in expected_levels:
        storey=byname.get(level['name'])
        if storey is None or storey.Elevation is None or abs(storey.Elevation*scale-level['elevation_m'])>0.50001e-6:raise ValueError('requested IFC storey name/elevation differs')
    if set(byname)-{l['name']for l in expected_levels}-{'Level 1'}:raise ValueError('unrequested IFC storey')
    storey_evidence=[{'name':s.Name,'elevation_metres':s.Elevation*scale}for s in storeys]

    walls=[r for r in report['records']if 'spec'in r];expected_guids={r['ifc_guid']for r in walls}
    if {w.GlobalId for w in models[1].by_type('IfcWall')}!=expected_guids:raise ValueError('IFC wall inventory differs')
    settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True);rows=[]
    for wall in walls:
        el=models[1].by_guid(wall['ifc_guid']);shape=ifcopenshell.geom.create_shape(settings,el,geometry_library='opencascade');g=shape.geometry
        points=np.asarray(g.verts).reshape((-1,3));faces=np.asarray(g.faces).reshape((-1,3));volume=ifcopenshell.util.shape.get_volume(g)
        projection=wall['ifc_projection'];dims=[projection['extrusion'][k]for k in('width_feet','depth_feet','height_feet')]
        origin=projection['location_feet'];angle=projection['rotation_radians']or 0
        c,t=math.cos(angle),math.sin(angle)
        projected=[[origin[0]+c*x-t*y,origin[1]+t*x+c*y,origin[2]+z]for x in(-dims[0]/2,dims[0]/2)for y in(-dims[1]/2,dims[1]/2)for z in(0,dims[2])]
        if not vertex_set_matches(projected,vertices(wall['spec']),1e-7):raise ValueError('public projection is not requested physical cuboid')
        # STEP writer rounds each metric origin/dimension and each direction
        # component to six decimals. Normalize the serialized basis as IFC does.
        six=lambda x:float(f'{x:.6f}')
        om=[six(x*.3048)for x in origin];dm=[six(x*.3048)for x in dims];axis=[six(c),six(t)];norm=math.hypot(*axis);c,t=[x/norm for x in axis]
        expected=[[om[0]+c*x-t*y,om[1]+t*x+c*y,om[2]+z]for x in(-dm[0]/2,dm[0]/2)for y in(-dm[1]/2,dm[1]/2)for z in(0,dm[2])]
        if not vertex_set_matches(points.tolist(),expected,1e-8):raise ValueError('STEP mesh vertices differ from independent serialized cuboid')
        if len(points)!=8 or len(faces)!=12:raise ValueError('STEP mesh topology differs')
        expected_volume=math.prod(dm);tri=points[faces];area=float(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1).sum()/2);expected_area=2*(dm[0]*dm[1]+dm[0]*dm[2]+dm[1]*dm[2])
        if abs(volume-expected_volume)>1e-8 or abs(area-expected_area)>1e-8:raise ValueError('STEP solid volume or area differs')
        yaw=math.radians(wall['spec'].get('yaw_degrees',0));quarter=None
        for q in (0,1,-1,2):
            expected_dims=[wall['spec']['length']/.3048,WIDTH,wall['spec']['height']/.3048]if q%2==0 else[WIDTH,wall['spec']['length']/.3048,wall['spec']['height']/.3048]
            if all(abs(a-b)<1e-7 for a,b in zip(dims,expected_dims))and abs(math.cos(angle)-math.cos(yaw+q*math.pi/2))<1e-7 and abs(math.sin(angle)-math.sin(yaw+q*math.pi/2))<1e-7:quarter=q;break
        if quarter is None:raise ValueError('unqualified material projection frame')
        placement=ifcopenshell.util.placement.get_local_placement(el.ObjectPlacement)
        if not np.allclose(placement[:3,0],[c,t,0],atol=1e-8,rtol=0)or not np.allclose(placement[:3,3],om,atol=1e-8,rtol=0):raise ValueError('STEP placement differs from serialized frame')
        rels=[r for r in el.HasAssociations if r.is_a('IfcRelAssociatesMaterial')]
        if len(rels)!=1 or not rels[0].RelatingMaterial.is_a('IfcMaterialLayerSetUsage'):raise ValueError('single material layer usage required')
        usage=rels[0].RelatingMaterial;layers=usage.ForLayerSet.MaterialLayers
        component=round(math.sin(quarter*math.pi/2))if quarter%2 else round(math.cos(quarter*math.pi/2))
        expected_axis='AXIS1'if quarter%2 else'AXIS2';expected_sense='NEGATIVE'if component>0 else'POSITIVE'
        if usage.LayerSetDirection!=expected_axis or usage.DirectionSense!=expected_sense or abs(usage.OffsetFromReferenceLine-component*.1)>1e-8:raise ValueError('material layer orientation/offset differs')
        if len(layers)!=1 or layers[0].Material is None or layers[0].Material.Name!='Default Wall'or abs(layers[0].LayerThickness-.2)>1e-8:raise ValueError('material or 200mm layer thickness differs')
        source_materials=[m for m in models[0].by_type('IfcMaterial')if m.Name=='Default Wall']
        if len(source_materials)!=1 or tuple(source_materials[0])!=tuple(layers[0].Material):raise ValueError('material differs from retained seed material')
        material={'name':layers[0].Material.Name,'thickness_metres':layers[0].LayerThickness,'axis':usage.LayerSetDirection,'sense':usage.DirectionSense,'offset_metres':usage.OffsetFromReferenceLine,'all_material_attributes_equal_seed':True}
        rows.append({'id':wall['id'],'ifc_guid':wall['ifc_guid'],'vertices_metres':points.tolist(),'triangles':faces.tolist(),'closed_volume_cubic_metres':volume,'surface_area_square_metres':area,'serialized_dimensions_metres':dm,'material':material,'independent_serialized_cuboid_matches':True})
    return {'candidate_sha256':report['candidate_sha256'],'ifcopenshell_version':ifcopenshell.version,'geometry_library':'opencascade','storeys':storey_evidence,'requested_storey_names_and_elevations_match':True,'schema_validation':schemas,'owner_history_controls':controls,'corrected_artifacts':artifacts,'source_walls':0,'candidate_walls':len(rows),'walls':rows,'autodesk_acceptance':'not_tested'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader',type=Path);p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/seed-document-verify-build');p.add_argument('--source',type=Path,default=Path(__file__).parent/'local/minimal_seed-Project.rvt');p.add_argument('--candidate',type=Path);p.add_argument('--plan',type=Path);p.add_argument('--request',type=Path);p.add_argument('--ifc-report',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.ifc_report:result=ifc_verify(json.loads(a.ifc_report.read_bytes()))
    else:
        if not all((a.reader,a.candidate,a.plan,a.request)):p.error('native verification requires --reader --candidate --plan --request')
        result=verify(a.reader,a.target,a.source,a.candidate,json.loads(a.plan.read_bytes()),json.loads(a.request.read_bytes()))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
