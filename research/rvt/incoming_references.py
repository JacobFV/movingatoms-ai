"""Bounded incoming ElementId audit: exact bytes prefilter, schema-directed decode.

Only pinned 2024 project records, all three channels. Embedded content groups
are outside project IDs. Unresolved routing and graph decodes remain explicit.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from element_table import decode as table_decode
from save_increments import decode as increments_decode
from partition_segments import decode as partition_decode
from partition_objects import validate
from increment_routing import select_record
from schema_probe import REV


def typed_hits(graph, declarations, targets):
    """Follow embedded schema declarations, never infer type from a field name."""
    classes={c['tag']:c for c in declarations};hits=[]
    def walk(tag,value,path,ancestry=()):
        if tag not in classes or not isinstance(value,dict):return
        c=classes[tag]
        if c['name']=='ElementId':
            ident=value.get('m_id',{}).get('m_id64')
            if ident in targets:hits.append({'target':ident,'path':path,'type':'ElementId','class_tag':tag})
            return
        if tag in ancestry:raise ValueError('cyclic class inheritance')
        parent=c['parent_reference']['tag']
        if parent:walk(parent,value,path,ancestry+(tag,))
        for f in c['fields']:
            v=value.get(f['name']);refs=f['references']
            # Pointer targets are traversed separately as graph objects.
            if f['base']!=14 or f['modifier']&1 or len(refs)!=1:continue
            child=refs[0]['tag'];p=path+'.'+f['name']
            if isinstance(v,list):
                for i,item in enumerate(v):walk(child,item,f'{p}[{i}]')
            else:walk(child,v,p)
    for i,obj in enumerate(graph['objects']):
        walk(obj['class_tag'],obj['fields'],f'objects[{i}]({obj["class_name"]}).fields')
    return hits


def numeric_hits(graph,targets):
    """Diagnostic scalar matches, explicitly not a typed reference assertion."""
    hits=[]
    def walk(value,path):
        if isinstance(value,dict):
            for name,item in value.items():walk(item,path+'.'+name)
        elif isinstance(value,list):
            for i,item in enumerate(value):walk(item,f'{path}[{i}]')
        elif type(value) is int and value in targets:hits.append({'value':value,'path':path})
    for i,obj in enumerate(graph['objects']):
        walk(obj['fields'],f'objects[{i}]({obj["class_name"]}).fields')
    return hits


def run(path,source,target,targets,catalog_path):
    source=source.resolve();target=target.resolve()
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    needles={i:struct.pack('<q',i) for i in targets}
    holders=defaultdict(dict);matches={};present=set();physical=0;embedded=0
    with olefile.OleFileIO(path) as f:
        def raw(name,offset=8):return zlib.decompress(unpage(f.openstream(name).read())[offset:],31)
        schema=raw('Formats/Latest',0)
        table=table_decode(raw('Global/ElemTable'),8)
        _,inc=increments_decode(raw('Global/DocumentIncrementTable'))
        if inc['m_permutation']:raise ValueError('permutation unsupported')
        increments=[{'greatest_episode':r['m_greatest']['m_id'],'stored_elements':r['m_totalElements'],
                     'redirects':[(v['m_causedByIncrementNumber'],v['m_totalElements']) for v in r['m_incrementVersions']]}for r in inc['m_increments']]
        for parts in f.listdir():
            if parts[0]!='Partitions':continue
            ordinal=int(parts[1]);present.add(ordinal)
            part=partition_decode(unpage(f.openstream(parts).read()))
            if part.root_tag!=0x37b:raise ValueError('requires 2024 profile')
            embedded+=len(part.segments)-1
            for seq,records in validate(part.segments[0],8).items():
                for record in records[:-1]:
                    physical+=1;holders[(record.element_id,seq)][ordinal]=True
                    found={i:[n for n in range(len(record.body)-7) if record.body[n:n+8]==needle] for i,needle in needles.items() if needle in record.body}
                    if found:matches[(record.element_id,seq,ordinal)]=(record.body,found)
    selected=[];unresolved=[];reasons=Counter();current=0
    for row in table.rows:
        element=table.current(row);episode=struct.unpack_from('<I',row,12)[0]
        for seq in (101,102,103):
            try:
                ordinal,reason=select_record(episode,increments,present,holders[(element,seq)])
                if reason=='sole_physical_holder_history_unresolved':raise ValueError(reason)
            except ValueError as e:
                unresolved.append({'element':element,'channel':seq,'diagnostic':str(e),'holders':sorted(holders[(element,seq)])});continue
            current+=1;reasons[reason]+=1
            if (element,seq,ordinal) in matches:
                body,found=matches[(element,seq,ordinal)]
                selected.append(({'element':element,'channel':seq,'stream':f'Partitions/{ordinal}',
                    'selection':reason,'body_sha256':hashlib.sha256(body).hexdigest(),'body_bytes':len(body),
                    'raw_target_offsets':found},body))
    local=Path(__file__).resolve().parent/'local'
    with tempfile.TemporaryDirectory(dir=local) as directory:
        project=Path(directory);(project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-incoming-references"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target)],check=True)
        (project/'schema').write_bytes(schema);paths=[]
        for n,(_,body) in enumerate(selected):
            out=project/f'body-{n}';out.write_bytes(body);paths.append(str(out))
        (project/'paths.json').write_text(json.dumps(paths))
        decoded=json.loads(subprocess.check_output([str(target/'release/rvt-incoming-references'),str(project/'schema'),str(catalog_path.resolve()),str(project/'paths.json')]))
    candidates=[]
    for (meta,_),result in zip(selected,decoded['records'],strict=True):
        item={**meta,'complete_graph':result['complete']}
        if result['complete']:
            graph=result['graph'];item.update(class_name=graph['objects'][0]['class_name'],objects=len(graph['objects']),
                typed_element_id_hits=typed_hits(graph,decoded['declarations'],targets),
                diagnostic_numeric_matches=numeric_hits(graph,targets))
        else:item['diagnostic']=result.get('diagnostic','incomplete byte consumption')
        candidates.append(item)
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reader_commit':REV,
        'schema_sha256':hashlib.sha256(schema).hexdigest(),'catalog_sha256':hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        'graph_limits':{'max_values':10000000,'max_objects':500000},'targets':targets,'project_elements':len(table.rows),'physical_project_records':physical,'current_records_selected':current,
        'selection_counts':dict(reasons),'embedded_groups_excluded':embedded,'unresolved_routes':unresolved,
        'candidate_records':candidates,'limits':['Only raw signed little-endian 64-bit target IDs are prefiltered; alternate encodings are not covered.',
        'Only project base groups are included; Global/Latest is audited separately.',
        'Typed matches are ElementId declarations reached through inline schema fields and graph objects; opaque values and unsupported graphs remain unresolved.',
        'A saved incoming reference does not by itself prove a new independent element must be added to that relationship.'],
        'highest_holder_fallback_used':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--catalog',type=Path,required=True);p.add_argument('--ids',type=int,nargs='+',default=[80437,20826]);a=p.parse_args()
    print(json.dumps(run(a.file,a.reader_source,a.target,a.ids,a.catalog),indent=2))
