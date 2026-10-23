"""Verify source-identical nominal length and actual parametric candidate graphs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from schema_probe import REV
from new_element_experiment import SOURCE_SHA
from wall_element import GraphEncoder
from wall_parametric import stretch_profile,encode_wall


def run(reader,source,candidate,target,length):
    reader=reader.resolve();target=target.resolve();source=source.resolve();candidate=candidate.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source pin differs')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader pin differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    profile_path=Path(__file__).parent/'results/wall-element-profile.json'
    profile=json.loads(profile_path.read_bytes())
    nominal,a=stretch_profile(profile,9.5)
    if nominal!=profile:raise ValueError('nominal length must preserve exact source graph')
    bodies,graphs,audit=encode_wall(profile,133210,length_feet=length,translation_xy=(400,0),context=profile['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local') as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('wall_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-element-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-wall-element-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        original=probe(source,20826)
        if original['summary']['current_records_outside_route'] or {str(r['channel']):r['graph'] for r in original['records']}!=profile['graphs']:
            raise ValueError('source current graphs differ')
        encoder=GraphEncoder(profile['declarations']);channels={}
        for record in original['records']:
            seq=str(record['channel']);raw=encoder.graph(nominal['graphs'][seq])
            if hashlib.sha256(raw).hexdigest()!=record['source']['body_sha256']:raise ValueError('source exact reconstruction failed')
            channels[seq]={'source_bytes':len(raw),'source_exact':True,'new_bytes':len(bodies[int(seq)]),
                'new_sha256':hashlib.sha256(bodies[int(seq)]).hexdigest(),'objects':len(graphs[seq]['objects']),'edges':len(graphs[seq]['edges'])}
        generated=probe(candidate,133210)
        if generated['summary']['current_records_outside_route'] or {str(r['channel']):r['graph'] for r in generated['records']}!=graphs:
            raise ValueError('actual candidate graphs differ from generated models')
        for record in generated['records']:
            if record['source']['body_sha256']!=channels[str(record['channel'])]['new_sha256']:raise ValueError('candidate actual body hash differs')
        retained=probe(candidate,20826)
        if {str(r['channel']):r['graph'] for r in retained['records']}!=profile['graphs']:raise ValueError('old wall changed')
        return {'source_sha256':SOURCE_SHA,'reader_revision':REV,'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            'candidate':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'source_nominal_length_reconstruction_exact':True,'actual_candidate_graphs_and_body_hashes_match':True,
            'original_wall_unchanged':True,'channels':channels,'geometry_audit':audit,
            'final_bbox_feet':graphs['103']['objects'][0]['fields']['m_bBox'],
            'scope':'Measured planar rectangular wall, world-axis-aligned; length varies, existing type/thickness/height/levels fixed.',
            'native_regeneration_semantics_proven':False,'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--length',type=float,default=12);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.reader_source,a.source,a.candidate,a.target,a.length)
    a.result.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('candidate_sha256','actual_candidate_graphs_and_body_hashes_match','final_bbox_feet')}))
