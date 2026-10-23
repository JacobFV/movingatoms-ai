"""Independent saved batch graphs, native BReps and emitted IFC geometry."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile

DEFAULT_SPECS=[{'element_id':133210,'length_feet':6.,'translation_xy':[400.,0.]},
               {'element_id':133211,'length_feet':12.,'translation_xy':[430.,0.]},
               {'element_id':133212,'length_feet':18.,'translation_xy':[470.,0.]}]


def expected_vertices(spec):
    """Independent rectangular solid coordinates; stretch, yaw about start, translate."""
    length=spec['length_feet'];xy=spec['translation_xy'];yaw=spec.get('yaw_degrees',0.)
    if not math.isfinite(length)or length<=0 or len(xy)!=2 or not all(math.isfinite(v)for v in xy)or not math.isfinite(yaw):raise ValueError('invalid finite dimensions/yaw')
    angle=math.radians(yaw);c,s=math.cos(angle),math.sin(angle)
    return [[119.5+xy[0]+c*x-s*y,67.75+xy[1]+s*x+c*y,76.+z]
            for x in (0.,length)for y in (-1/3,1/3)for z in (0.,15.)]


def expected_bounds(spec):
    points=expected_vertices(spec)
    return [[min(p[i]for p in points)for i in range(3)],[max(p[i]for p in points)for i in range(3)]]


def vertex_set_matches(actual,expected,tolerance):
    if len(actual)!=len(expected):return False
    unmatched=list(expected)
    for point in actual:
        matching=[i for i,p in enumerate(unmatched)if near(point,p,tolerance)]
        if len(matching)!=1:return False
        unmatched.pop(matching[0])
    return not unmatched


def validate_specs(specs):
    ids=[s['element_id']for s in specs]
    if not specs or len(ids)!=len(set(ids)):raise ValueError('unique batch IDs required')
    for s in specs:
        if type(s['element_id'])is not int or s['element_id']<=0:raise ValueError('positive native IDs required')
        expected_bounds(s)


def near(left,right,tolerance=1e-7):
    return len(left)==len(right)and all(math.isfinite(x)and math.isfinite(y)and abs(x-y)<=tolerance for x,y in zip(left,right))


def projection_frame(spec,wall):
    """Accept only a proven quarter-turn reparameterization of the requested cuboid."""
    bounds=expected_bounds(spec);origin=[(bounds[0][i]+bounds[1][i])/2 for i in range(2)]+[76.]
    if not near(wall['location_feet'],origin):raise ValueError('projected origin differs')
    actual=wall['rotation_radians']or 0.;yaw=math.radians(spec.get('yaw_degrees',0.));length=spec['length_feet']
    dimensions=[wall['extrusion'][k]for k in('width_feet','depth_feet','height_feet')]
    for quarter in (0,1,-1,2):
        angle=yaw+quarter*math.pi/2;dims=[length,2/3,15.]if quarter%2==0 else[2/3,length,15.]
        if near(dimensions,dims)and near([math.cos(actual),math.sin(actual)],[math.cos(angle),math.sin(angle)]):
            frame={'quarter_turns':quarter,'origin_feet':origin,'angle_radians':angle,'dimensions_feet':dims}
            c,t=math.cos(angle),math.sin(angle)
            vertices=[[origin[0]+c*x-t*y,origin[1]+t*x+c*y,origin[2]+z]for x in(-dims[0]/2,dims[0]/2)for y in(-dims[1]/2,dims[1]/2)for z in(0,dims[2])]
            if not vertex_set_matches(vertices,expected_vertices(spec),1e-7):raise ValueError('projected frame is not physically equivalent')
            return frame
    raise ValueError('projected dimensions/basis differ from requested solid')


def serialized_oracle(spec,frame):
    """Independently reproduce documented six-decimal STEP numeric fields."""
    def six(value):return float(f'{value:.6f}')
    origin=[six(v*.3048)for v in frame['origin_feet']];angle=frame['angle_radians']
    raw=[six(math.cos(angle)),six(math.sin(angle))];size=math.hypot(*raw);axis=[v/size for v in raw]
    dims=[six(v*.3048)for v in frame['dimensions_feet']];c,t=axis
    vertices=[[origin[0]+c*x-t*y,origin[1]+t*x+c*y,origin[2]+z]for x in(-dims[0]/2,dims[0]/2)for y in(-dims[1]/2,dims[1]/2)for z in(0,dims[2])]
    eps=.5e-6;direction_bound=math.sqrt(2)*eps;normalized_axis_bound=2*direction_bound/(1-direction_bound)
    bound=math.sqrt(3)*eps+math.sqrt(1.5)*eps+math.hypot(dims[0]/2,dims[1]/2)*normalized_axis_bound
    emitted_angle=math.atan2(axis[1],axis[0]);angle_error=math.atan2(math.sin(emitted_angle-angle),math.cos(emitted_angle-angle))
    return {'origin_metres':origin,'x_axis':axis+[0.],'dimensions_metres':dims,'vertices_metres':vertices,
            'decimal_places':6,'requested_yaw_degrees':spec.get('yaw_degrees',0.),'equivalent_profile_yaw_degrees':math.degrees(angle),
            'serialized_profile_yaw_degrees':math.degrees(emitted_angle),'profile_angular_error_radians':angle_error,
            'ideal_vertex_deviation_bound_metres':bound,'bound_derivation':'sqrt(3)*epsilon + sqrt(1.5)*epsilon + half-diagonal*2*sqrt(2)*epsilon/(1-sqrt(2)*epsilon), epsilon=0.5e-6'}


def native_verify(reader,target,source,candidate,profile,specs):
    import olefile,zlib
    from codec import decode as unpage
    from save_candidate import unpack_global
    from schema_probe import REV
    from wall_parametric import encode_wall
    from new_element_registration import semantic_graph
    from wall_brep_audit import audit_graph,face_polygon,resolver
    validate_specs(specs);reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=profile['source_sha256']:raise ValueError('source hash mismatch')
    if profile['reader_revision']!=REV or subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=candidate.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir();probe_source=Path(__file__).with_name('wall_candidate_probe.rs').read_bytes();(work/'src/main.rs').write_bytes(probe_source)
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-batch-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-wall-batch-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        indexes=[];parts=[]
        for path in(source,candidate):
            with olefile.OleFileIO(path)as f:
                schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
                if hashlib.sha256(schema).hexdigest()!=profile['schema_sha256']:raise ValueError('schema changed')
                (work/'schema.bin').write_bytes(schema)
                for stream,name in [('Global/ElemTable','index'),('Global/History','history')]:
                    (work/(name+'.bin')).write_bytes(unpack_global(unpage(f.openstream(stream).read()))[0])
                indexes.append(probe('identity',work/'schema.bin',work/'index.bin',work/'history.bin')['identities'])
                parts.append({'/'.join(s):hashlib.sha256(f.openstream(s).read()).hexdigest()for s in f.listdir()if s[0]=='Partitions'})
        old,new=indexes;ids={str(s['element_id'])for s in specs}
        if set(new)!=set(old)|ids or any(new[k]!=v for k,v in old.items()):raise ValueError('prior identities changed')
        if len({v['unique_id']for v in new.values()})!=len(new):raise ValueError('duplicate native UniqueId')
        if set(parts[1])!=set(parts[0])|{'Partitions/66'}or any(parts[1][k]!=v for k,v in parts[0].items()):raise ValueError('prior partition changed')
        rows=[];all_records=[]
        for spec in specs:
            ident=spec['element_id'];result=probe(candidate,ident)
            if result['summary']['current_records_outside_route']or len(result['records'])!=3:raise ValueError('batch routing incomplete')
            encoder=encode_wall;extra={}
            if spec.get('yaw_degrees',0):
                from wall_oriented import encode_wall as oriented_encode
                encoder=oriented_encode;extra={'yaw_degrees':spec['yaw_degrees']}
            bodies,graphs,_=encoder(profile,ident,length_feet=spec['length_feet'],translation_xy=spec['translation_xy'],context=profile['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True,**extra)
            records={r['channel']:r for r in result['records']}
            if set(records)!={101,102,103}:raise ValueError('batch channel inventory differs')
            channels={}
            for ch,r in records.items():
                g=r['graph']
                if r['identity']['element_id']!=ident or r['source']['stream']!='Partitions/66'or not g or g['consumed_bytes']!=r['source']['body_bytes']:raise ValueError('incomplete batch graph')
                if semantic_graph(g)!=semantic_graph(graphs[str(ch)])or r['source']['body_sha256']!=hashlib.sha256(bodies[ch]).hexdigest():raise ValueError('batch body semantics differ')
                channels[str(ch)]={'objects':len(g['objects']),'edges':len(g['edges']),'bytes':g['consumed_bytes'],'sha256':r['source']['body_sha256']}
            brep=audit_graph(records[103]['graph']);bounds=brep['native_vertex_bounds_feet'];expected=expected_bounds(spec)
            if not all(near(a,b)for a,b in zip(bounds,expected))or abs(brep['closed_solid_volume_cubic_feet']-spec['length_feet']*10)>1e-7:raise ValueError('saved native BRep dimensions/volume differ')
            solids=[g for g in brep['geometry_components']if g['closed']]
            if len(solids)!=1:raise ValueError('expected one closed native solid')
            native_vertices=[];resolve=resolver(records[103]['graph'])
            for face in solids[0]['face_loops']:
                polygon,_,_=face_polygon(records[103]['graph'],face['face_object'],resolve)
                for point in polygon:
                    if not any(near(point,p)for p in native_vertices):native_vertices.append(point)
            if not vertex_set_matches(native_vertices,expected_vertices(spec),1e-7):raise ValueError('native rotated vertex set differs')
            length=spec['length_feet'];area=2*(length*(2/3)+length*15+(2/3)*15)
            if abs(solids[0]['surface_area_square_feet']-area)>1e-7:raise ValueError('native surface area differs')
            brep['expected_transformed_vertex_set_matches']=True;brep['expected_closed_surface_area_square_feet']=area
            outlines=[o['fields']['m_minmax']for o in records[101]['graph']['objects']if o['class_name']=='Outline']
            if len(outlines)!=1 or not all(near(a,b)for a,b in zip(outlines[0],bounds)):raise ValueError('header bounds differ from native BRep')
            rows.append({'spec':spec,'native_identity':new[str(ident)],'channels':channels,'native_brep':brep,'header_outline_matches_brep':True});all_records.extend(result['records'])
        decode={'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'reader_revision':REV,'probe_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'probe_source_sha256':hashlib.sha256(probe_source).hexdigest(),'records':all_records}
        decoded=candidate.with_name(candidate.stem+'-independent-graphs.json');decoded.write_text(json.dumps(decode,indent=2)+'\n')
        projections=[];artifacts=[]
        for label,path in [('source',source),('candidate',candidate)]:
            out=work/(label+'.ifc');projections.append(probe('projection',path,out));data=out.read_bytes();artifact=candidate.with_name(candidate.stem+'-'+label+'.ifc')
            if artifact.exists()and artifact.read_bytes()!=data:raise ValueError('IFC artifact differs')
            if not artifact.exists():artifact.write_bytes(data)
            artifacts.append({'file':artifact.name,'sha256':hashlib.sha256(data).hexdigest()})
        before,after=projections;a={e['type_guid']:e for e in before['entities']};b={e['type_guid']:e for e in after['entities']}
        if set(b)!=set(a)|ids or any(b[k]!=v for k,v in a.items()):raise ValueError('prior projected entities changed')
        if any(after['native_ids'].get(k)!=v for k,v in before['native_ids'].items()):raise ValueError('prior native IFC GUID changed')
        if len(set(after['native_ids'].values()))!=len(after['native_ids']):raise ValueError('duplicate IFC GUID')
        for row in rows:
            ident=str(row['spec']['element_id']);wall=b[ident]
            row['ifc_projection_frame']=projection_frame(row['spec'],wall)
            row['ifc_rotation_radians']=wall['rotation_radians']or 0.
            row['native_ifc_guid']=after['native_ids'][ident]
        return {'source_sha256':profile['source_sha256'],'candidate_sha256':decode['candidate_sha256'],'reader_revision':REV,'prior_native_identities_preserved':len(old),'original_partitions_unchanged':len(parts[0]),
                'prior_projected_entities_preserved':len(a),'native_and_ifc_identifiers_unique':True,'walls':rows,'ifc_artifacts':artifacts,
                'independent_graphs_file':decoded.name,'independent_graphs_sha256':hashlib.sha256(decoded.read_bytes()).hexdigest(),'autodesk_acceptance':'not_tested','complete_save_transaction':False}


def ifc_verify(source,candidate,native_report,mesh_result):
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    import ifcopenshell.util.placement
    import ifcopenshell.validate
    import numpy as np
    from wall_candidate_ifc_owner_control import correct
    from wall_parametric_candidate_ifc import check_dimensions
    for path,artifact in zip((source,candidate),native_report['ifc_artifacts']):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=artifact['sha256']:raise ValueError('STEP differs from native export evidence')
    def schema(path):
        model=ifcopenshell.open(str(path));logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(model,logger,express_rules=True)
        return {'file':path.name,'schema':model.schema,'messages':[{'level':s.get('level'),'message':s.get('message'),'instance':str(s.get('instance'))}for s in logger.statements]}
    raw_schema=[schema(p)for p in(source,candidate)]
    corrected=[p.with_name(p.stem+'-owner-corrected.ifc')for p in(source,candidate)]
    controls=[correct(p,out)for p,out in zip((source,candidate),corrected)]
    corrected_schema=[schema(p)for p in corrected]
    if any(row['messages']for row in corrected_schema):raise ValueError('corrected batch IFC has schema errors')
    settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True);meshes=[];models=[]
    for path in corrected:
        model=ifcopenshell.open(str(path));models.append(model);rows={}
        for wall in model.by_type('IfcWall'):
            if wall.GlobalId in rows:raise ValueError('duplicate IFC wall GUID')
            shape=ifcopenshell.geom.create_shape(settings,wall,geometry_library='opencascade');g=shape.geometry
            rows[wall.GlobalId]=(np.asarray(g.verts).reshape((-1,3)),list(g.faces),ifcopenshell.util.shape.get_volume(g))
        meshes.append(rows)
    old,new=meshes;new_ids={w['native_ifc_guid']for w in native_report['walls']}
    if len(new_ids)!=len(native_report['walls'])or set(new)!=set(old)|new_ids:raise ValueError('batch IFC wall inventory differs')
    for guid,(vertices,faces,volume)in old.items():
        if not np.array_equal(new[guid][0],vertices)or new[guid][1]!=faces or new[guid][2]!=volume:raise ValueError('old wall mesh changed')
    rows=[];mesh_rows=[]
    def mesh_row(label,guid,ident,path,index):
        v,f,_=meshes[index][guid]
        return {'label':label,'native_element_id':ident,'ifc_guid':guid,'file':path.name,'step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'vertices':v.tolist(),'triangles':[f[i:i+3]for i in range(0,len(f),3)]}
    sourcewalls=[w for w in models[0].by_type('IfcWall')if w.Name.endswith(':20826')]
    if len(sourcewalls)!=1:raise ValueError('ambiguous sourcewallmesh')
    sourcewall=sourcewalls[0];mesh_rows.append(mesh_row('source',sourcewall.GlobalId,20826,corrected[0],0))
    for wall in native_report['walls']:
        spec=wall['spec'];guid=wall['native_ifc_guid'];v,f,volume=new[guid];minimum=v.min(axis=0).tolist();maximum=v.max(axis=0).tolist()
        frame=wall['ifc_projection_frame'];oracle=serialized_oracle(spec,frame)
        expected_points=oracle['vertices_metres'];c,s=oracle['x_axis'][:2]
        if not vertex_set_matches(v.tolist(),expected_points,1e-8):raise ValueError('IFC serialized rotated vertex set differs')
        origin=np.asarray(oracle['origin_metres']);relative=v-origin
        local=np.column_stack((c*relative[:,0]+s*relative[:,1],-s*relative[:,0]+c*relative[:,1],relative[:,2]))
        dims=oracle['dimensions_metres']
        shape=check_dimensions(local.min(axis=0).tolist(),local.max(axis=0).tolist(),volume,[d/.3048 for d in dims])
        triangles=v[np.asarray(f).reshape((-1,3))]
        area=float(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1).sum()/2)
        expected_area=2*(dims[0]*dims[1]+dims[0]*dims[2]+dims[1]*dims[2])
        if abs(area-expected_area)>1e-8:raise ValueError('IFC rotated surface area differs')
        ideal=[[x*.3048 for x in p]for p in expected_vertices(spec)]
        deviation=max(min(math.dist(point,p)for p in ideal)for point in v.tolist())
        if deviation>oracle['ideal_vertex_deviation_bound_metres']+1e-8:raise ValueError('STEP quantization exceeds independently derived bound')
        shape.update(expected_transformed_vertex_set_matches=True,surface_area_square_metres=area,expected_surface_area_square_metres=expected_area,
            yaw_degrees=spec.get('yaw_degrees',0.),dimensions_basis='validated equivalent serialized profile axes',
            requested_dimensions_metres=[spec['length_feet']*.3048,(2/3)*.3048,15*.3048],
            maximum_ideal_vertex_deviation_metres=deviation,serialization_oracle=oracle)
        if len(v)!=8 or len(f)!=36:raise ValueError('batch mesh topology differs')
        element=models[1].by_guid(guid)
        placement=ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
        if not near(placement[:3,0].tolist(),oracle['x_axis'],1e-8)or not near(placement[:3,3].tolist(),oracle['origin_metres'],1e-8):raise ValueError('IFC explicit serialized placement/rotation differs')
        shape['placement_x_axis']=placement[:3,0].tolist();shape['placement_origin_metres']=placement[:3,3].tolist()
        rels=[r for r in element.HasAssociations if r.is_a('IfcRelAssociatesMaterial')]
        if len(rels)!=1 or not rels[0].RelatingMaterial.is_a('IfcMaterialLayerSetUsage'):raise ValueError('batch layer usage missing')
        usage=rels[0].RelatingMaterial;quarter=frame['quarter_turns']
        component=round(math.sin(quarter*math.pi/2))if quarter%2 else round(math.cos(quarter*math.pi/2))
        expected_layer_axis='AXIS1'if quarter%2 else'AXIS2'
        expected_sense='NEGATIVE'if component>0 else'POSITIVE'
        if usage.LayerSetDirection!=expected_layer_axis or usage.DirectionSense!=expected_sense or abs(usage.OffsetFromReferenceLine-component*.1016)>1e-8:
            raise ValueError('material layer axis/sense/offset differs from requested thickness normal')
        shape['material_layer_axis']=usage.LayerSetDirection;shape['material_layer_direction_sense']=usage.DirectionSense
        layers=usage.ForLayerSet.MaterialLayers
        if len(layers)!=1 or layers[0].Material.Name!='Default Wall'or abs(layers[0].LayerThickness-.2032)>1e-8:raise ValueError('batchmaterial differs')
        rows.append({'element_id':spec['element_id'],'native_ifc_guid':guid,'minimum_metres':minimum,'maximum_metres':maximum,
                     'shape':shape,'vertices':8,'triangles':12,'material_name':layers[0].Material.Name,'layer_thickness_metres':layers[0].LayerThickness})
        mesh_rows.append(mesh_row('new',guid,spec['element_id'],corrected[1],1))
    mesh_evidence={'kind':'Actual batch IFC projection meshes, not Revit UI','units':'metres','coordinates':'world','ifcopenshell_version':ifcopenshell.version,'kernel':'opencascade','meshes':mesh_rows,
                   'native_candidate_sha256':native_report['candidate_sha256']}
    mesh_result.write_text(json.dumps(mesh_evidence,indent=2)+'\n')
    return {'candidate_sha256':native_report['candidate_sha256'],'native_candidate_sha256':native_report['candidate_sha256'],'source_ifc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_ifc_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'ifcopenshell_version':ifcopenshell.version,'kernel':'opencascade','units':'metres','raw_schema_validation':raw_schema,
            'explicit_owner_history_correction_controls':controls,'corrected_schema_validation':corrected_schema,
            'existing_wall_meshes_exactly_unchanged':len(old),'candidate_wall_count':len(new),'new_walls':rows,
            'mesh_evidence_file':mesh_result.name,'mesh_evidence_sha256':hashlib.sha256(mesh_result.read_bytes()).hexdigest(),
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'Actual emitted IFC triangulation. Native BRep consistency is separately audited from saved channel103 graphs; neither establishes Autodesk acceptance.',
            'autodesk_acceptance':'not_tested','complete_save_transaction':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--reader-source',type=Path);p.add_argument('--target',type=Path);p.add_argument('--plan',type=Path)
    p.add_argument('--ifc',action='store_true');p.add_argument('--native-report',type=Path);p.add_argument('--result',type=Path,required=True);p.add_argument('--mesh-result',type=Path)
    a=p.parse_args()
    if a.ifc:
        if a.native_report is None:p.error('--ifc requires --native-report')
        result=ifc_verify(a.source,a.candidate,json.loads(a.native_report.read_bytes()),a.mesh_result or a.result.with_name(a.result.stem+'-meshes.json'))
    else:
        if any(x is None for x in(a.reader_source,a.target,a.plan)):p.error('native verification requires --reader-source --target --plan')
        plan=json.loads(a.plan.read_bytes());specs=[{'element_id':w['id'],**w['spec']}for w in plan['walls']]
        profile=json.loads(Path(__file__).with_name('results').joinpath('wall-element-profile.json').read_bytes())
        result=native_verify(a.reader_source,a.target,a.source,a.candidate,profile,specs)
        result['plan_sha256']=hashlib.sha256(a.plan.read_bytes()).hexdigest()
    tmp=a.result.with_name(a.result.name+'.tmp');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(a.result)
    print(json.dumps({'result':str(a.result),'autodesk_acceptance':'not_tested'}))
