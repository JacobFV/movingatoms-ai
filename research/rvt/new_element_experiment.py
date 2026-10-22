"""Build and independently decode a fresh DataStorage payload and identity row."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
import zlib
import olefile
from codec import decode as unpage
from verify_element_tables import inflate
import element_table
import save_history
from partition_segments import decode as partition_decode, encode as partition_encode
from partition_objects import validate, Record
from partition_builder import build_partition
from schema_probe import REV
from new_element import data_storage, allocate_identity

SOURCE_SHA='c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'
EPISODE=uuid.UUID('562a3df0-6022-5912-aeb1-33b6a875b44e')
STORAGE=uuid.UUID('7cd7ab1f-7535-5cd6-a873-a3af417c6e4d')
NAME='Clean-room DataStorage Δ'


def sha(data): return hashlib.sha256(data).hexdigest()

def references(value,path=''):
    found=[]
    if isinstance(value,dict):
        for k,v in value.items():
            if k=='m_id64': found.append({'path':path+'.'+k,'id':v})
            else: found+=references(v,path+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):found+=references(v,path+f'[{i}]')
    return found


def run(reader,source,target):
    reader=reader.resolve();source=source.resolve();target=target.resolve()
    if sha(source.read_bytes())!=SOURCE_SHA:raise ValueError('requires pinned core2024 fixture')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    local=Path(__file__).parent/'local'
    with tempfile.TemporaryDirectory(dir=local) as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('new_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-new-element-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-new-element-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        original=probe(source,80437)
        storage_inventory=probe(source,'class:DataStorage')
        serialized_guids=[]
        for record in storage_inventory['records']:
            if record['graph'] is None: raise ValueError('incomplete DataStorage inventory')
            for obj in record['graph']['objects']:
                fields=obj['fields']
                if fields.get('schema_name')=='DataStorageUniqueId':
                    serialized_guids.append(bytes(fields['fields'][0]['raw_value']['m_guid']['guid_bytes']))
        if STORAGE.bytes_le in serialized_guids: raise ValueError('storage GUID collision')
        if original['summary']['current_records_outside_route'] or len(original['records'])!=3:
            raise ValueError('source must have exact three-channel routing')
        catalog=original['summary']['extensible_storage_catalog']
        (work/'catalog.json').write_text(json.dumps(catalog))
        with olefile.OleFileIO(source) as f:
            schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
            (work/'schema.bin').write_bytes(schema)
            raw_index=inflate(unpage(f.openstream('Global/ElemTable').read()))
            raw_history=inflate(unpage(f.openstream('Global/History').read()))
            partition=partition_decode(unpage(f.openstream('Partitions/46').read()))
        records=validate(partition.segments[0],8)
        bodies={seq:next(r.body for r in rs if r.element_id==80437) for seq,rs in records.items()}
        (work/'source.bin').write_bytes(bodies[102])
        declaration_probe=probe('decode',work/'schema.bin',work/'source.bin',work/'catalog.json')
        allclasses={c['tag']:c for c in declaration_probe['declarations']}
        seen=set();todo=[c['tag'] for c in allclasses.values() if c['name'] in
            ('DataStorage','ElementHeader','ElementParents','SerializedDummy','CellList','ESEntityCell','ElemRec','IdentifierSource')]
        while todo:
            tag=todo.pop()
            if not tag or tag in seen:continue
            seen.add(tag);c=allclasses[tag];todo.append(c['parent_reference']['tag'])
            todo.extend(r['tag'] for f in c['fields'] for r in f['references'])
        declarations=[allclasses[t] for t in sorted(seen)]
        rebuilt=data_storage(declarations,catalog,80437,'','d5ec174e-6367-4b6c-acc6-aa3b9894332b')
        if rebuilt!=bodies:raise ValueError('source reconstruction differs')
        table=element_table.decode(raw_index,8);history=save_history.decode(raw_history)
        ident,newtable=allocate_identity(table,history)
        newhistory=save_history.prepend_episode(history,EPISODE.bytes_le)
        generated=data_storage(declarations,catalog,ident,NAME,STORAGE)
        decoded={};audits={}
        for seq,body in generated.items():
            path=work/f'body-{seq}.bin';path.write_bytes(body)
            result=probe('decode',work/'schema.bin',path,work/'catalog.json')
            graph=result['graph'];refs=references([o['fields'] for o in graph['objects']])
            if any(r['id'] not in (-1,ident) for r in refs):raise ValueError('unexpected outgoing reference')
            if graph['consumed_bytes']!=len(body):raise ValueError('incomplete generated body')
            decoded[str(seq)]=graph
            audits[str(seq)]={'bytes':len(body),'sha256':sha(body),'objects':len(graph['objects']),
                              'edges':len(graph['edges']),'element_references':refs}
        root=decoded['102']['objects'][0]['fields']
        if root['m_name']!=NAME or root['m_id']['m_id']['m_id64']!=ident:raise ValueError('new fields differ')
        dynamic=decoded['102']['objects'][-1]['fields']['fields'][0]['raw_value']['m_guid']['guid_bytes']
        if bytes(dynamic)!=STORAGE.bytes_le:raise ValueError('storage GUID differs')
        identities=[]
        for prefix,index_bytes,history_bytes in [('old',raw_index,raw_history),('new',element_table.encode(newtable),save_history.encode(newhistory))]:
            (work/(prefix+'-index.bin')).write_bytes(index_bytes)
            (work/(prefix+'-history.bin')).write_bytes(history_bytes)
            identities.append(probe('identity',work/'schema.bin',work/(prefix+'-index.bin'),work/(prefix+'-history.bin')))
        # Preserve all existing independently derived identities exactly.
        old,new=identities
        oldrows=old['identities'];newrows=new['identities']
        expected=f'{EPISODE}-{ident:08x}'
        if len(newrows)!=len(oldrows)+1 or any(newrows[k]!=v for k,v in oldrows.items()):
            raise ValueError('existing identity changed')
        fresh=newrows[str(ident)]
        if fresh['unique_id']!=expected or fresh['creation_episode']!=history.next_sequence:
            raise ValueError('new creation identity differs')
        built=build_partition(partition.root_tag,{s:(Record(ident,b),) for s,b in generated.items()},8,allow_unsigned_nonempty=True)
        payload=partition_encode(built)
        if partition_decode(payload)!=built:raise ValueError('new partition did not round trip')
        # Keep the checked-in schema evidence small: transitive declarations used by the encoder.
        bytag={c['tag']:c for c in declarations};seen=set();todo=[c['tag'] for c in declarations if c['name'] in
            ('DataStorage','ElementHeader','ElementParents','SerializedDummy','CellList','ESEntityCell','ElemRec','IdentifierSource')]
        while todo:
            tag=todo.pop()
            if not tag or tag in seen:continue
            seen.add(tag);c=bytag[tag];todo.append(c['parent_reference']['tag'])
            todo.extend(r['tag'] for f in c['fields'] for r in f['references'])
        profile={'source_sha256':SOURCE_SHA,'schema_sha256':sha(schema),'reader_revision':REV,
                 'declarations':[bytag[t] for t in sorted(seen)],
                 'catalog':{'schemas':{k:v for k,v in catalog['schemas'].items() if k in ('8de41042-7da6-4d45-afb4-f8e5ba779816','4147c867-cdfe-42fd-808f-3bbafda73da5')}}}
        result={'source_file':source.name,'source_sha256':SOURCE_SHA,'reader_revision':REV,
                'schema_sha256':sha(schema),'source_element':80437,
                'source_channel_reconstruction':{str(s):{'bytes':len(b),'sha256':sha(b),'byte_identical':True} for s,b in bodies.items()},
                'current_datastorage_guid_count':len(serialized_guids),'generated_storage_guid_absent_from_current_datastorage':True,
                'generated_name':NAME,'generated_id':ident,'generated_storage_guid':str(STORAGE),
                'generated_episode':history.next_sequence,'generated_episode_guid':str(EPISODE),
                'source_identity_count':len(oldrows),'new_identity_count':len(newrows),
                'existing_identities_unchanged':True,'new_identity':fresh,'channels':audits,
                'decoded_graphs':decoded,'partition_payload_bytes':len(payload),'partition_sha256':sha(payload),
                'limits':['Only pinned core2024 profile and its two existing ES schemas are supported.',
                          'Header flag values and document pointer token follow observed DataStorage; creation semantics remain unproven.',
                          'No whole RVT is emitted; incoming indexes, registration, save bookkeeping and signature acceptance are not established.',
                          'Fresh IDs/GUIDs are unique in this experiment; callers must check allocator state and GUID collisions before integration.'],
                'autodesk_acceptance':'not_tested','complete_save_transaction':False}
        return result,profile

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('source',type=Path);p.add_argument('--result',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True);a=p.parse_args()
    result,profile=run(a.reader_source,a.source,a.target)
    a.result.write_text(json.dumps(result,indent=2)+'\n');a.profile.write_text(json.dumps(profile,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('generated_id','generated_episode','new_identity_count','channels')},indent=2))
