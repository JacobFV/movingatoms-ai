"""Reproduce source-exact seed Level encoding and independent body decoding."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from partition_segments import decode as partition_decode
from partition_objects import validate
from schema_probe import REV
from seed_level import SOURCE_SHA, encode_level
from verify_element_tables import inflate
from wall_element import GraphEncoder


def audit(source, reader, target):
    source=source.resolve();reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    root=Path(__file__).parent
    with tempfile.TemporaryDirectory(dir=root/'local') as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes((root/'wall_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-seed-level-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-seed-level-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        current=probe(source,1916)
        if len(current['records'])!=3 or current['summary']['current_records_outside_route']:raise ValueError('source routes differ')
        graphs={str(r['channel']):r['graph'] for r in current['records']}
        with olefile.OleFileIO(source) as f:
            schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
            partition=partition_decode(unpage(f.openstream('Partitions/0').read()))
        bodies={}
        for segment in partition.segments:
            for channel,records in validate(segment,8).items():
                for record in records:
                    if record.element_id==1916:
                        if channel in bodies:raise ValueError('ambiguous source record')
                        bodies[channel]=record.body
        (work/'schema.bin').write_bytes(schema);(work/'body.bin').write_bytes(bodies[102])
        declarations=probe('decode',work/'schema.bin',work/'body.bin')['declarations']
        bytag={c['tag']:c for c in declarations};todo=[o['class_tag'] for g in graphs.values() for o in g['objects']];seen=set()
        def refs(field):
            yield from (r['tag'] for r in field['references'])
            if field['nested_descriptor']:yield from refs(field['nested_descriptor'])
        while todo:
            tag=todo.pop()
            if not tag or tag in seen:continue
            seen.add(tag);c=bytag[tag];todo.append(c['parent_reference']['tag'])
            for field in c['fields']:todo.extend(refs(field))
        profile={'source_sha256':SOURCE_SHA,'reader_revision':REV,'schema_sha256':hashlib.sha256(schema).hexdigest(),'graphs':graphs,'declarations':[bytag[t] for t in sorted(seen)]}
        encoder=GraphEncoder(profile['declarations'])
        for channel,body in bodies.items():
            if encoder.graph(graphs[str(channel)])!=body:raise ValueError('source graph roundtrip differs')
        if encode_level(profile,1916,'Level 1',0,acknowledge_lifecycle_hypothesis=True)!=bodies:raise ValueError('zero-edit parameter roundtrip differs')
        variants=[]
        for ident,name,elevation in [(1916,'Ground Δ',0),(2301,'Upper floor',12.5),(2302,'Basement',-10),(2303,'Roof 😀',30)]:
            generated=encode_level(profile,ident,name,elevation,acknowledge_lifecycle_hypothesis=True)
            decoded={}
            for channel,body in generated.items():
                (work/'body.bin').write_bytes(body)
                graph=probe('decode',work/'schema.bin',work/'body.bin')['graph']
                if graph['consumed_bytes']!=len(body) or encoder.graph(graph)!=body:raise ValueError('generated decoder roundtrip differs')
                decoded[str(channel)]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'objects':len(graph['objects']),'edges':len(graph['edges'])}
                if channel==102:
                    level=graph['objects'][0]['fields']
                    if level['m_text']!=name or level['m_id']['m_id']['m_id64']!=ident:raise ValueError('decoded name/identity differs')
                    if [o['fields']['m_origin'][2] for o in graph['objects'] if o['class_name']=='Plane'] != [elevation,elevation]:raise ValueError('plane elevation differs')
            variants.append({'element_id':ident,'name':name,'elevation_feet':elevation,'channels':decoded})
        incoming=probe('incoming',source,1916)
        # Compare independently decoded real nonzero levels and level trackers.
        comparison=root/'local/core2024.rvt'
        comparison_sha='c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'
        if hashlib.sha256(comparison.read_bytes()).hexdigest()!=comparison_sha:raise ValueError('comparison source mismatch')
        controls=probe(comparison,'class:Level')
        level_controls=[]
        for record in controls['records']:
            if record['channel']!=102:continue
            f=record['graph']['objects'][0]['fields']
            level_controls.append({'id':record['identity']['element_id'],'name':f['m_text'],
                'plane_origins':[o['fields']['m_origin'] for o in record['graph']['objects'] if o['class_name']=='Plane'],
                'bubble_end':f['m_bubbleEnd'],'free_end':f['m_freeEnd'],'new_view_reference_points':f['m_refPointsForNewViews']})
        global_controls=[]
        def find_id(value,path=''):
            if isinstance(value,dict):
                for key,item in value.items():yield from find_id(item,path+'.'+key)
            elif isinstance(value,list):
                for i,item in enumerate(value):yield from find_id(item,path+f'[{i}]')
            elif type(value)is int and value==1916:yield path
        for native in (source,comparison):
            with olefile.OleFileIO(native) as f:
                fmt=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
                raw=inflate(unpage(f.openstream('Global/Latest').read()))
            if raw[-4:]!=bytes(4):raise ValueError('unqualified Global footer')
            (work/'schema.bin').write_bytes(fmt);(work/'body.bin').write_bytes(raw[:-4])
            gg=probe('decode',work/'schema.bin',work/'body.bin')['graph']
            maps=[o['fields']['m_levelIdToPlanViewIds'] for o in gg['objects'] if o['class_name']=='LevelPlanViewTracking']
            hits=[{'object':i,'class':o['class_name'],'paths':list(find_id(o['fields']))} for i,o in enumerate(gg['objects']) if list(find_id(o['fields']))]
            global_controls.append({'source_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'global_inflated_sha256':hashlib.sha256(raw).hexdigest(),'complete_objects':len(gg['objects']),'level_plan_maps':maps,'seed_id_references':hits if native==source else []})

        report={'comparison_source_sha256':comparison_sha,'nonzero_level_controls':level_controls,'global_controls':global_controls,'incoming_references':incoming,'source_sha256':SOURCE_SHA,'reader_revision':REV,'schema_sha256':profile['schema_sha256'],'source_identity':current['records'][0]['identity'],'source_channels':{str(c):{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'reconstruction_exact':True} for c,b in bodies.items()},'variants':variants,'limits':['Bodies only: no save or native application acceptance tested.','New IDs in this audit are illustrative, not an allocation contract.','Both horizontal surface origins updated; zero annotation/reference-point caches preserved as an explicit hypothesis.','Retains seed LevelAttributes1910; Global level registration and dependent views require separate audit.','Public typed Level decoder expects m_name/m_elevation; this actual schema uses m_text and Plane origins, so typed projection alone cannot validate this profile.']}
        return profile,report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=Path(__file__).parent/'local/minimal_seed-Project.rvt');p.add_argument('--reader',type=Path,required=True);p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/seed_level-build');a=p.parse_args()
    profile,report=audit(a.source,a.reader,a.target)
    for suffix,data in [('profile',profile),('audit',report)]:
        (Path(__file__).parent/'results'/f'seed_level-{suffix}.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(report,indent=2))
