"""Independent complete native graphs, identity, preservation and IFC wall projection."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
from wall_candidate import EPISODE
from new_element_experiment import SOURCE_SHA
from schema_probe import REV
from wall_element import translated_wall
from new_element_registration import semantic_graph


def numeric_equal(left,right,tolerance=1e-10):
    if type(left)in(int,float) and type(right)in(int,float):return abs(left-right)<=tolerance
    if isinstance(left,dict) and isinstance(right,dict):return set(left)==set(right) and all(numeric_equal(v,right[k],tolerance)for k,v in left.items())
    if isinstance(left,list) and isinstance(right,list):return len(left)==len(right) and all(numeric_equal(a,b,tolerance)for a,b in zip(left,right))
    return left==right


def projection_check(before,after,translation=(30.0,20.0)):
    def index(report):
        rows=report['entities'];result={e['type_guid']:e for e in rows}
        if len(result)!=len(rows) or None in result:raise ValueError('ambiguous projected element IDs')
        return result
    old,new=index(before),index(after)
    if set(new)!=set(old)|{'133210'}:raise ValueError('unexpected projected element inventory')
    for ident,entity in old.items():
        if new[ident]!=entity:raise ValueError(f'existing projected element changed: {ident}')
    source,created=old['20826'],new['133210']
    if source['ifc_type']!=created['ifc_type'] or 'WALL' not in source['ifc_type'].upper():raise ValueError('not a wall projection')
    position=source['location_feet'];expected=[position[0]+translation[0],position[1]+translation[1],position[2]]
    if any(abs(x-y)>1e-10 for x,y in zip(created['location_feet'],expected)):raise ValueError('IFC translated placement differs')
    for key in ('extrusion','rotation_radians','solid_shape','storey_index','host_element_index'):
        if not numeric_equal(source.get(key),created.get(key)):raise ValueError(f'IFC dimensions/context changed: {key}')
    if source['extrusion'] is None:raise ValueError('missing actual extrusion')
    material_fields=('material_index','material_layer_set_index','material_profile_set_index')
    material_changes={k:{'source':source.get(k),'new':created.get(k)}for k in material_fields if source.get(k)!=created.get(k)}
    if any(after['native_ids'].get(k)!=v for k,v in before['native_ids'].items()):raise ValueError('existing native projected GUID changed')
    return {'existing_projected_elements_unchanged':len(old),'source_wall_count':sum('WALL' in e['ifc_type'].upper()for e in old.values()),
            'candidate_wall_count':sum('WALL' in e['ifc_type'].upper()for e in new.values()),'source_location_feet':position,
            'new_location_feet':created['location_feet'],'translation_feet':list(translation)+[0],
            'source_extrusion':source['extrusion'],'new_extrusion':created['extrusion'],'floating_geometry_tolerance_feet':1e-10,'new_native_ifc_guid':after['native_ids'].get('133210'),
            'material_projection_changes':material_changes,'source_layers':before['layers'].get('20826'),'new_layers':after['layers'].get('133210'),'material_projection_unchanged':not material_changes and before['layers'].get('20826')==after['layers'].get('133210'),'unchanged_rotation':source['rotation_radians'],'existing_native_projected_guids_preserved':True}


def verify(reader,target,source,candidate,profile,translation=(30.0,20.0),room_bounding=True):
    reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source mismatch')
    if profile['source_sha256']!=SOURCE_SHA or profile['reader_revision']!=REV:raise ValueError('profile provenance mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    expected_bodies,expected_graphs,_,_=translated_wall(profile,133210,translation,profile['external_references'],room_bounding=None if room_bounding else False,acknowledge_bounding_hypothesis=not room_bounding)
    with tempfile.TemporaryDirectory(dir=source.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir();(work/'src/main.rs').write_bytes(Path(__file__).with_name('wall_candidate_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-candidate-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        def probe(*args):return json.loads(subprocess.check_output([str(target/'release/rvt-wall-candidate-probe'),*map(str,args)]))
        indexes=[];parts=[];globals_raw=[]
        for path in (source,candidate):
            with olefile.OleFileIO(path)as f:
                schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
                if hashlib.sha256(schema).hexdigest()!=profile['schema_sha256']:raise ValueError('schema changed')
                (work/'schema.bin').write_bytes(schema)
                for stream,name in [('Global/ElemTable','index'),('Global/History','history')]:
                    (work/(name+'.bin')).write_bytes(unpack_global(unpage(f.openstream(stream).read()))[0])
                globals_raw.append(unpack_global(unpage(f.openstream('Global/Latest').read()))[0])
                indexes.append(probe('identity',work/'schema.bin',work/'index.bin',work/'history.bin')['identities'])
                parts.append({'/'.join(s):hashlib.sha256(f.openstream(s).read()).hexdigest()for s in f.listdir()if s[0]=='Partitions'})
        old,new=indexes
        if set(new)!=set(old)|{'133210'} or any(new[k]!=v for k,v in old.items()):raise ValueError('old identity changed')
        if new['133210']['unique_id']!=f'{EPISODE}-0002085a':raise ValueError('new unique ID differs')
        if set(parts[1])!=set(parts[0])|{'Partitions/66'} or any(parts[1][k]!=v for k,v in parts[0].items()):raise ValueError('old partitions changed')
        from wall_element_registration import register,verify_graph
        registration=json.loads(Path(__file__).with_name('results').joinpath('wall-element-registration.json').read_bytes())
        expected_global,change=register(globals_raw[0],registration,133210)
        if globals_raw[1]!=expected_global:raise ValueError('actual candidate registration differs')
        source_record=probe(source,20826)
        (work/'catalog.json').write_text(json.dumps(source_record['summary']['extensible_storage_catalog']))
        global_graphs=[]
        for label,raw in zip(('before','after'),globals_raw):
            if raw[-4:]!=b'\0'*4:raise ValueError('unknown Global terminator')
            (work/(label+'.bin')).write_bytes(raw[:-4])
            global_graphs.append(probe('decode',work/'schema.bin',work/(label+'.bin'),work/'catalog.json')['graph'])
        verify_graph(*global_graphs,change)
        current=probe(candidate,133210)
        if current['summary']['current_records_outside_route'] or len(current['records'])!=3:raise ValueError('new current routing incomplete')
        channels={}
        for record in current['records']:
            ch=record['channel'];g=record['graph']
            if record['source']['stream']!='Partitions/66' or not g or g['consumed_bytes']!=record['source']['body_bytes']:raise ValueError('incomplete new graph')
            if semantic_graph(g)!=semantic_graph(expected_graphs[str(ch)]):raise ValueError('unexpected native graph differences')
            if record['source']['body_sha256']!=hashlib.sha256(expected_bodies[ch]).hexdigest():raise ValueError('new encoded body differs')
            channels[str(ch)]={'objects':len(g['objects']),'edges':len(g['edges']),'bytes':g['consumed_bytes'],'sha256':record['source']['body_sha256']}
        exports=[];reports=[]
        for label,path in [('source',source),('candidate',candidate)]:
            out=work/(label+'.ifc');reports.append(probe('projection',path,out))
            data=out.read_bytes();saved=candidate.parent/(candidate.stem+'-'+label+'.ifc')
            if saved.exists() and saved.read_bytes()!=data:raise ValueError('existing IFC artifact differs')
            if not saved.exists():saved.write_bytes(data)
            exports.append({'file':saved.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        projection=projection_check(*reports,translation=translation)
        return {'source_sha256':SOURCE_SHA,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'reader_revision':REV,
                'prior_native_identities_unchanged':len(old),'new_identity':new['133210'],'original_partitions_byte_identical':len(parts[0]),'actual_global_registration_verified':True,'global_graph_objects':len(global_graphs[1]['objects']),
                'complete_new_channels':channels,'ifc_projection':projection,'ifc_step_artifacts':exports,'room_bounding':room_bounding,'material_scanner_diagnostic':probe('material-route',candidate),'autodesk_acceptance':'not_tested',
                'complete_save_transaction':False,'all_incoming_registration_rules_proven':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--translation',type=float,nargs=2,default=(30.0,20.0));p.add_argument('--non-room-bounding',action='store_true');p.add_argument('--profile',type=Path,default=Path(__file__).parent/'results/wall-element-profile.json');a=p.parse_args()
    print(json.dumps(verify(a.reader_source,a.target,a.source,a.candidate,json.loads(a.profile.read_bytes()),a.translation,not a.non_room_bounding),indent=2))
