"""Independent parametric graphs with byte-exact binding to the outside control."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import olefile
from new_element_registration import semantic_graph
from schema_probe import REV


def streams(path):
    with olefile.OleFileIO(path)as f:return {'/'.join(s):f.openstream(s).read()for s in f.listdir()}


def verify(reader,target,control,candidate,profile,control_evidence):
    from wall_parametric import encode_wall
    reader=reader.resolve();target=target.resolve()
    if control_evidence['candidate_sha256']!=hashlib.sha256(control.read_bytes()).hexdigest():raise ValueError('control evidence hash mismatch')
    if control_evidence['reader_revision']!=REV or profile['reader_revision']!=REV:raise ValueError('evidence reader revision mismatch')
    if control_evidence['source_sha256']!=profile['source_sha256']:raise ValueError('source evidence differs')
    if not control_evidence['actual_global_registration_verified']or control_evidence['room_bounding']is not False:raise ValueError('requires verified nonbounding outside control')
    old,new=streams(control),streams(candidate)
    if old.keys()!=new.keys():raise ValueError('stream inventory differs')
    changes=[name for name in old if old[name]!=new[name]]
    if changes!=['Partitions/66']:raise ValueError('parametric candidate changes streams beyond new partition')
    bodies,graphs,*_=encode_wall(profile,133210,length_feet=12.0,translation_xy=(400.0,0.0),context=profile['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=candidate.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir();(work/'src/main.rs').write_bytes(Path(__file__).with_name('wall_candidate_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-parametric-candidate-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        def probe(*args):return json.loads(subprocess.check_output([str(target/'release/rvt-wall-parametric-candidate-probe'),*map(str,args)]))
        current=probe(candidate,133210)
        if current['summary']['current_records_outside_route'] or len(current['records'])!=3:raise ValueError('parametric routing incomplete')
        channels={}
        for record in current['records']:
            ch=record['channel'];graph=record['graph']
            if record['source']['stream']!='Partitions/66' or not graph or graph['consumed_bytes']!=record['source']['body_bytes']:raise ValueError('parametric graph incomplete')
            if semantic_graph(graph)!=semantic_graph(graphs[str(ch)]):raise ValueError('unexpected parametric native semantics')
            digest=hashlib.sha256(bodies[ch]).hexdigest()
            if record['source']['body_sha256']!=digest:raise ValueError('parametric body differs')
            channels[str(ch)]={'objects':len(graph['objects']),'edges':len(graph['edges']),'body_sha256':digest,'body_bytes':len(bodies[ch])}
        export=work/'parametric.ifc';projection=probe('projection',candidate,export)
        prior=probe('projection',control)
        oldentities={e['type_guid']:e for e in prior['entities']};newentities={e['type_guid']:e for e in projection['entities']}
        if oldentities.keys()!=newentities.keys():raise ValueError('unexpected projected element inventory')
        if any(newentities[k]!=v for k,v in oldentities.items()if k!='133210'):raise ValueError('existing projected entity changed')
        if prior['native_ids']!=projection['native_ids']:raise ValueError('native IFC identity changed')
        wall=newentities['133210'];extrusion=wall['extrusion']
        expected={'width_feet':12.0,'depth_feet':2/3,'height_feet':15.0}
        if any(abs(extrusion[k]-v)>1e-10 for k,v in expected.items()):raise ValueError('parametric IFC dimensions differ')
        if any(abs(x-y)>1e-10 for x,y in zip(wall['location_feet'],[525.5,67.75,76])):raise ValueError('parametric IFC location differs')
        artifact=candidate.with_suffix('.ifc');data=export.read_bytes()
        if artifact.exists() and artifact.read_bytes()!=data:raise ValueError('IFC artifact exists with different bytes')
        if not artifact.exists():artifact.write_bytes(data)
        return {'source_sha256':profile['source_sha256'],'control_sha256':hashlib.sha256(control.read_bytes()).hexdigest(),
                'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'reader_revision':REV,
                'control_evidence_sha256':hashlib.sha256(json.dumps(control_evidence,sort_keys=True).encode()).hexdigest(),
                'changed_streams_from_control':changes,'all_other_streams_byte_identical':True,
                'prior_native_identities_preserved_via_byte_identical_tables':control_evidence['prior_native_identities_unchanged'],
                'actual_registration_preserved_from_verified_control':True,'complete_new_channels':channels,
                'prior_projected_entities_exactly_preserved':len(oldentities)-1,'all_native_ifc_ids_preserved':True,
                'parametric_extrusion':extrusion,'location_feet':wall['location_feet'],
                'ifc_file':artifact.name,'ifc_sha256':hashlib.sha256(data).hexdigest(),'new_native_ifc_guid':projection['native_ids']['133210'],
                'complete_save_transaction':False,'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('control',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args();results=Path(__file__).parent/'results'
    print(json.dumps(verify(a.reader_source,a.target,a.control,a.candidate,json.loads((results/'wall-element-profile.json').read_bytes()),json.loads((results/'wall-candidate-outside-verification.json').read_bytes())),indent=2))
