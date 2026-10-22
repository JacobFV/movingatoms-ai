"""Independent source reconstruction and translated wall graph/geometry audit."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from partition_segments import decode as partition_decode
from partition_objects import validate
from verify_element_tables import inflate
from new_element_experiment import references,SOURCE_SHA
from schema_probe import REV
from wall_element import GraphEncoder,translated_wall
from wall_element_registration import register,verify_graph


def run(reader,source,target,profile,candidate=None,new_id=133210,translation=(30.0,20.0),room_bounding=None):
    reader=reader.resolve();source=source.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('pinned source required')
    if profile['source_sha256']!=SOURCE_SHA or profile['reader_revision']!=REV:raise ValueError('profile provenance mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local') as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('wall_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-element-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-wall-element-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        current=probe(source,20826)
        if current['summary']['current_records_outside_route'] or len(current['records'])!=3:raise ValueError('source routing must be exact')
        actual={str(r['channel']):r['graph'] for r in current['records']}
        if actual!=profile['graphs']:raise ValueError('source profile graphs differ')
        context=[]
        for expected in profile['context']:
            extracted=probe(source,expected['id'])
            record=next(r for r in extracted['records'] if r['channel']==102)
            if extracted['summary']['current_records_outside_route'] or record['graph'] is None or record['identity']!=expected['identity'] or record['class_name']!=expected['class']:
                raise ValueError('existing context is not the verified current identity')
            context.append({'id':expected['id'],'class':expected['class'],'unique_id':record['identity']['unique_id']})
        with olefile.OleFileIO(source) as f:
            schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
            partition=partition_decode(unpage(f.openstream('Partitions/59').read()))
            global_raw=inflate(unpage(f.openstream('Global/Latest').read()))
        if hashlib.sha256(schema).hexdigest()!=profile['schema_sha256']:raise ValueError('embedded schema differs')
        (work/'schema.bin').write_bytes(schema)
        records=validate(partition.segments[0],8)
        source_bodies={seq:next(r.body for r in rs if r.element_id==20826) for seq,rs in records.items()}
        encoder=GraphEncoder(profile['declarations'])
        for seq,raw in source_bodies.items():
            if encoder.graph(actual[str(seq)])!=raw:raise ValueError('source body reconstruction differs')
        bodies,graphs,moves,identities=translated_wall(profile,new_id,translation,profile['external_references'],room_bounding=room_bounding,acknowledge_bounding_hypothesis=room_bounding is not None)
        decoded={};channels={}
        for seq,raw in bodies.items():
            (work/'body.bin').write_bytes(raw)
            graph=probe('decode',work/'schema.bin',work/'body.bin')['graph']
            if graph!=graphs[str(seq)]:raise ValueError('generated graph differs')
            refs=references([o['fields'] for o in graph['objects']])
            if any(r['id']>0 and r['id']not in profile['external_references']+[new_id] for r in refs):raise ValueError('unexpected outgoing reference')
            decoded[str(seq)]=graph
            channels[str(seq)]={'source_bytes':len(source_bodies[seq]),'source_sha256':hashlib.sha256(source_bodies[seq]).hexdigest(),
                'source_reconstruction_exact':True,'new_bytes':len(raw),'new_sha256':hashlib.sha256(raw).hexdigest(),
                'objects':len(graph['objects']),'edges':len(graph['edges']),'references':refs}
        (work/'global-before.bin').write_bytes(global_raw[:-4])
        before=probe('decode',work/'schema.bin',work/'global-before.bin')
        obj=next(o for o in before['objects'] if o['class_name']=='StructuralElemSetTracking')
        evidence={'source_sha256':SOURCE_SHA,'reader_revision':REV,'inflated_sha256':hashlib.sha256(global_raw).hexdigest(),'object':obj}
        changed,change=register(global_raw,evidence,new_id)
        (work/'global-after.bin').write_bytes(changed[:-4])
        after=probe('decode',work/'schema.bin',work/'global-after.bin')
        verify_graph(before['graph'],after['graph'],change)
        ifc_before=probe('geometry',source,20826)
        candidate_report=None
        if candidate:
            native=probe(candidate,new_id)
            if native['summary']['current_records_outside_route'] or {str(r['channel']):r['graph'] for r in native['records']}!=decoded:raise ValueError('actual candidate wall differs')
            old=probe(candidate,20826)
            if {str(r['channel']):r['graph'] for r in old['records']}!=actual:raise ValueError('old wall changed')
            with olefile.OleFileIO(candidate) as f:
                candidate_global=inflate(unpage(f.openstream('Global/Latest').read()))
            if candidate_global!=changed:raise ValueError('actual candidate registration differs')
            ifc_after=probe('geometry',candidate,new_id)
            a,b=ifc_before['entity'],ifc_after['entity']
            def close(x,y):
                if type(x)in (int,float) and type(y)in (int,float):return math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-10)
                if isinstance(x,dict) and isinstance(y,dict):return set(x)==set(y) and all(close(x[k],y[k]) for k in x)
                if isinstance(x,list) and isinstance(y,list):return len(x)==len(y) and all(close(u,v) for u,v in zip(x,y))
                return x==y
            for key in ('extrusion','rotation_radians','solid_shape','ifc_type','storey_index'):
                if not close(a[key],b[key]):raise ValueError('unexpected IFC shape/level change: '+key)
            materials=('material_index','material_layer_set_index','material_profile_set_index')
            material_projection={k:{'before':a[k],'after':b[k]} for k in materials}
            material_unchanged=all(a[k]==b[k] for k in materials)
            delta=[b['location_feet'][i]-a['location_feet'][i] for i in range(3)]
            if not all(math.isclose(delta[i],(*translation,0)[i],abs_tol=1e-10) for i in range(3)):raise ValueError('IFC displacement differs')
            candidate_report={'file':candidate.name,'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                'all_three_graphs_match_generated':True,'original_wall_graphs_unchanged':True,
                'registration_payload_exact':True,'ifc_location_delta_feet':delta,'ifc_dimensions_level_unchanged':True,'ifc_material_projection_unchanged':material_unchanged,'material_projection':material_projection,'ifc':ifc_after}
        return {'source_sha256':SOURCE_SHA,'reader_revision':REV,'source_wall':20826,'new_id':new_id,
            'translation_xy_feet':translation,'room_bounding_override':room_bounding,'bounding_toggle_lifecycle_proven':False if room_bounding is not None else None,'channels':channels,'world_coordinate_changes':moves,'self_identity_changes':identities,
            'verified_existing_context':context,'source_ifc':ifc_before,'actual_candidate':candidate_report,
            'registration':{'objects':len(after['graph']['objects']),'edges':len(after['graph']['edges']),
                'growth_bytes':len(changed)-len(global_raw),'only_structural_id_set_changed':True},
            'limits':['Measured straight unjoined Basic Wall only; all type/level/material references are explicit existing context.',
                'Topology/flags/cache defaults are re-encoded from named source graph values, not inferred universal creation defaults.',
                'Source room tag, view override and LevelRoomPlan references remain attached to original wall; new room-bounding topology regeneration is unresolved.',
                'Independent graph/IFC decoding does not establish Autodesk acceptance.'],'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('source',type=Path)
    p.add_argument('--profile',type=Path,default=Path(__file__).parent/'results/wall-element-profile.json')
    p.add_argument('--candidate',type=Path);p.add_argument('--new-id',type=int,default=133210)
    p.add_argument('--non-room-bounding',action='store_true');p.add_argument('--translation',type=float,nargs=2,default=(30,20));p.add_argument('--result',type=Path,required=True)
    a=p.parse_args();r=run(a.reader_source,a.source,a.target,json.loads(a.profile.read_bytes()),a.candidate,a.new_id,a.translation,False if a.non_room_bounding else None)
    a.result.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'channels':{k:(v['objects'],v['edges']) for k,v in r['channels'].items()},'registration':r['registration'],'candidate_verified':r['actual_candidate']is not None}))
