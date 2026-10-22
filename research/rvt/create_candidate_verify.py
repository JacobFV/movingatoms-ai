"""Independent native identity, three-channel and preservation checks for creation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
from new_element_experiment import SOURCE_SHA,EPISODE,STORAGE,NAME,references
from schema_probe import REV
from partition_segments import decode as partition_decode
from partition_objects import validate
import basic_file_info_codec


def verify(reader,target,source,candidate):
    reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=source.parent)as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('new_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-create-candidate-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-create-candidate-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        indexes=[];old_streams={};bfi=[];candidate_streams=set();global_hashes=[]
        for label,path in [('source',source),('candidate',candidate)]:
            with olefile.OleFileIO(path)as f:
                schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
                (work/'schema.bin').write_bytes(schema)
                for stream,name in [('Global/ElemTable','index'),('Global/History','history')]:
                    (work/(name+'.bin')).write_bytes(unpack_global(unpage(f.openstream(stream).read()))[0])
                indexes.append(probe('identity',work/'schema.bin',work/'index.bin',work/'history.bin')['identities'])
                bfi.append(basic_file_info_codec.decode(f.openstream('BasicFileInfo').read()))
                global_hashes.append(hashlib.sha256(unpack_global(unpage(f.openstream('Global/Latest').read()))[0]).hexdigest())
                for stream in f.listdir():
                    name='/'.join(stream)
                    if not name.startswith('Partitions/'):continue
                    raw=f.openstream(stream).read()
                    if label=='source':old_streams[name]=hashlib.sha256(raw).hexdigest()
                    else:candidate_streams.add(name)
                    if label=='candidate' and name in old_streams and hashlib.sha256(raw).hexdigest()!=old_streams[name]:raise ValueError('existing partition changed')
                if label=='candidate':
                    records=validate(partition_decode(unpage(f.openstream('Partitions/66').read())).segments[0],8)
                    if any([r.element_id for r in rs]!=[133210,2**64-1]for rs in records.values()):raise ValueError('unexpected new record IDs')
        if candidate_streams != set(old_streams)|{'Partitions/66'}:raise ValueError('unexpected partition stream inventory')
        old,new=indexes
        if len(new)!=len(old)+1 or any(new.get(k)!=v for k,v in old.items()):raise ValueError('existing identity changed')
        identity=new['133210']
        if identity['unique_id']!=f'{EPISODE}-0002085a':raise ValueError('new UniqueId mismatch')
        current=probe(candidate,133210)
        if current['summary']['current_records_outside_route'] or len(current['records'])!=3:raise ValueError('new record routing incomplete')
        channels={}
        for record in current['records']:
            if record['source']['stream']!='Partitions/66' or record['graph'] is None:raise ValueError('wrong source or incomplete graph')
            graph=record['graph'];refs=references([o['fields']for o in graph['objects']])
            if any(r['id'] not in (-1,133210)for r in refs):raise ValueError('unexpected outgoing element reference')
            if graph['consumed_bytes']!=record['source']['body_bytes']:raise ValueError('incomplete graph consumption')
            channels[str(record['channel'])]={'objects':len(graph['objects']),'edges':len(graph['edges']),
                'bytes':graph['consumed_bytes'],'references':refs,'body_sha256':record['source']['body_sha256']}
            if record['channel']==102:
                if graph['objects'][0]['fields']['m_name']!=NAME:raise ValueError('new name mismatch')
                values=[bytes(o['fields']['fields'][0]['raw_value']['m_guid']['guid_bytes'])for o in graph['objects']if o['fields'].get('schema_name')=='DataStorageUniqueId']
                if values!=[STORAGE.bytes_le]:raise ValueError('new storage GUID mismatch')
        expected=json.loads(Path(__file__).with_name('results').joinpath('new-element.json').read_bytes())
        if expected['source_sha256']!=SOURCE_SHA or expected['reader_revision']!=REV:
            raise ValueError('new-body reference evidence mismatch')
        for channel,data in channels.items():
            if data['body_sha256']!=expected['channels'][channel]['sha256']:
                raise ValueError('new body differs from independently schema-checked encoder result')
        inventory=probe(source,'class:DataStorage')
        storage_guids=[bytes(o['fields']['fields'][0]['raw_value']['m_guid']['guid_bytes'])for r in inventory['records']if r['graph']for o in r['graph']['objects']if o['fields'].get('schema_name')=='DataStorageUniqueId']
        if STORAGE.bytes_le in storage_guids:raise ValueError('storage GUID collision')
        if bfi[1].increments!=67 or bfi[1].guid!=str(EPISODE):raise ValueError('save identity differs')
        if basic_file_info_codec.encode(bfi[1],bfi[0].increments,bfi[0].guid)!=bfi[0].source:raise ValueError('unrelated BFI bytes changed')
        registration=json.loads(Path(__file__).with_name('results').joinpath('new-element-registration.json').read_bytes())
        if registration['source_evidence']['source_file_sha256']!=SOURCE_SHA or registration['source_evidence']['inflated_sha256']!=global_hashes[0]:
            raise ValueError('registration source evidence mismatch')
        if global_hashes[1] not in (global_hashes[0],registration['new_inflated_sha256']):
            raise ValueError('unexpected Global/Latest bytes')
        registered=global_hashes[1]==registration['new_inflated_sha256']
        return {'source_sha256':SOURCE_SHA,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                'reader_commit':REV,'prior_native_identities_preserved':len(old),'new_native_identity':identity,
                'original_partition_streams_unchanged':len(old_streams),'new_channels':channels,
                'source_datastorage_guids_checked':len(storage_guids),'new_storage_guid_unique':True,
                'basic_file_info_all_identity_copies_synchronized':True,'opaque_basic_file_info_bytes_preserved':True,
                'root_registration_known_three_lists_updated':registered,
                'registration_full_graph_evidence_bound_by_sha256':registered,
                'registration_graph_objects':registration['objects_after'] if registered else None,
                'all_possible_registration_rules_proven':False,
                'autodesk_acceptance':'not_tested','complete_save_transaction':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    a=p.parse_args();print(json.dumps(verify(a.reader_source,a.target,a.source,a.candidate),indent=2))
