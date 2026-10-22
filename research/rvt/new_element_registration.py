"""Guarded append to the three measured incoming DataStorage registration lists.

The source evidence must come from an independent full Global/Latest decode.
This is an experimental registration operation, not a complete save algorithm.
"""
from copy import deepcopy
import hashlib
import struct
import uuid
from new_element import FDX, UNIQUE
from new_element_experiment import references


def id_set_bytes(values):
    return struct.pack('<I',len(values))+b''.join(struct.pack('<q',v) for v in values)


def extended_set(raw,span,values,new_id):
    if values!=sorted(set(values)) or new_id in values:
        raise ValueError('ID set must be sorted unique and new ID absent')
    start,end=span['start'],span['end']
    if not 0<=start<end<=len(raw) or raw[start:end]!=id_set_bytes(values):
        raise ValueError('schema span does not match actual ID set bytes')
    return start,end,id_set_bytes(sorted(values+[new_id]))


def register(raw,evidence,new_id,source_id=80437):
    if hashlib.sha256(raw).hexdigest()!=evidence['inflated_sha256']:
        raise ValueError('Global/Latest source hash mismatch')
    if type(new_id) is not int or not 0<new_id<2**63-1:
        raise ValueError('invalid new element ID')
    objects=evidence['objects'];byname={o['class_name']:o for o in objects}
    if len(objects)!=2 or set(byname)!={'ElemsSetWithCellsTracking','EStorageTracking'}:
        raise ValueError('requires exactly two unique registration objects')
    patches=[];changes=[]
    generic=byname['ElemsSetWithCellsTracking']
    maps=generic['fields']['m_elemIdSetMap']
    spans=[s for s in generic['field_spans'] if s['name']=='m_idSet']
    if len(spans)!=len(maps):raise ValueError('cell tracking spans disagree')
    matches=[(i,m) for i,m in enumerate(maps) if m['first']==-100]
    if len(matches)!=1:raise ValueError('requires unique measured -100 cell registration')
    i,m=matches[0];values=[v['m_id']['m_id64'] for v in m['second']['m_idSet']]
    if source_id not in values:raise ValueError('source not registered in cell set')
    patches.append(extended_set(raw,spans[i],values,new_id))
    changes.append({'class_name':generic['class_name'],'field':'m_elemIdSetMap','item_index':i,
                    'ids_before':values,'ids_after':sorted(values+[new_id]),'span_before':spans[i]})
    storage=byname['EStorageTracking'];items=storage['fields']['m_trackingItems']
    spans=[s for s in storage['field_spans'] if s['name']=='m_elemIdSet']
    if len(spans)!=len(items):raise ValueError('ES tracking spans disagree')
    seen=set()
    for i,item in enumerate(items):
        guid=str(uuid.UUID(bytes_le=bytes(item['m_schemaGuid']['m_guid']['guid_bytes'])))
        if guid not in (FDX,UNIQUE):continue
        if guid in seen:raise ValueError('duplicate tracked ES schema')
        seen.add(guid);values=[v['m_id']['m_id64'] for v in item['m_elemIdSet']]
        if source_id not in values:raise ValueError('source not registered in ES set')
        patches.append(extended_set(raw,spans[i],values,new_id))
        changes.append({'class_name':storage['class_name'],'field':'m_trackingItems','item_index':i,
                        'schema_guid':guid,'ids_before':values,'ids_after':sorted(values+[new_id]),'span_before':spans[i]})
    if seen!={FDX,UNIQUE}:raise ValueError('missing ES registration')
    patches.sort()
    if any(a[1]>b[0] for a,b in zip(patches,patches[1:])):raise ValueError('overlapping ID arrays')
    result=raw
    for start,end,replacement in reversed(patches):result=result[:start]+replacement+result[end:]
    return result,changes


def semantic_graph(graph):
    def fields(value):
        if isinstance(value,list):return [fields(v) for v in value]
        if isinstance(value,dict):
            return {k:fields(v) for k,v in value.items() if not (k=='offset' and ('pointer_token' in value or 'discriminator' in value))}
        return value
    return {'objects':[{'class_name':o['class_name'],'class_tag':o['class_tag'],'token':o['token'],'fields':fields(o['fields'])} for o in graph['objects']],
            'edges':[{k:v for k,v in e.items() if k!='pointer_offset'} for e in graph['edges']]}


def verify_graph(before,after,changes,new_id):
    expected=semantic_graph(before)
    for change in changes:
        matching=[o for o in expected['objects'] if o['class_name']==change['class_name']]
        if len(matching)!=1:raise ValueError('ambiguous registration graph object')
        item=matching[0]['fields'][change['field']][change['item_index']]
        values=[{'m_id':{'m_id64':v}} for v in change['ids_after']]
        if change['class_name']=='ElemsSetWithCellsTracking':item['second']['m_idSet']=values
        else:item['m_elemIdSet']=values
    if expected!=semantic_graph(after):raise ValueError('unexpected Global/Latest semantic difference')
    hits=[r for o in after['objects'] for r in references(o['fields']) if r['id']==new_id]
    if len(hits)!=3:raise ValueError('expected exactly three new incoming references')
    return hits


def experiment(reader,source,target,candidate=None):
    import json
    from pathlib import Path
    import subprocess
    import tempfile
    import zlib
    import olefile
    from codec import decode as unpage
    from verify_element_tables import inflate
    from schema_probe import REV
    from new_element_experiment import SOURCE_SHA
    reader=reader.resolve();target=target.resolve();source=source.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('requires pinned core2024 fixture')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local') as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('new_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-new-element-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-new-element-probe'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        with olefile.OleFileIO(source) as f:
            schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
            raw=inflate(unpage(f.openstream('Global/Latest').read()))
        if raw[-4:]!=b'\0'*4:raise ValueError('unsupported Global/Latest terminator')
        (work/'schema.bin').write_bytes(schema)
        current=probe(source,80437)
        (work/'catalog.json').write_text(json.dumps(current['summary']['extensible_storage_catalog']))
        (work/'before.bin').write_bytes(raw[:-4])
        before=probe('decode',work/'schema.bin',work/'before.bin',work/'catalog.json')
        objects=[o for o in before['objects'] if o['class_name'] in ('ElemsSetWithCellsTracking','EStorageTracking')]
        evidence={'source_file_sha256':SOURCE_SHA,'inflated_sha256':hashlib.sha256(raw).hexdigest(),
                  'schema_sha256':hashlib.sha256(schema).hexdigest(),'reader_revision':REV,'objects':objects}
        new,changes=register(raw,evidence,133210)
        candidate_evidence=None
        if candidate is not None:
            with olefile.OleFileIO(candidate) as f:
                candidate_stored=f.openstream('Global/Latest').read()
                candidate_raw=inflate(unpage(candidate_stored))
                candidate_schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
            if candidate_raw!=new or candidate_schema!=schema:
                raise ValueError('actual candidate Global/Latest or schema differs from verified registration')
            candidate_evidence={'file':candidate.name,'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                'latest_stored_sha256':hashlib.sha256(candidate_stored).hexdigest(),
                'latest_inflated_sha256':hashlib.sha256(candidate_raw).hexdigest(),
                'actual_candidate_payload_exactly_matches_registration':True}
            new=candidate_raw
        (work/'after.bin').write_bytes(new[:-4])
        after=probe('decode',work/'schema.bin',work/'after.bin',work/'catalog.json')
        hits=verify_graph(before['graph'],after['graph'],changes,133210)
        return {'actual_candidate':candidate_evidence,'source_evidence':evidence,'new_element':133210,'changes':changes,
                'before_bytes':len(raw),'after_bytes':len(new),'byte_growth':len(new)-len(raw),
                'objects_before':len(before['graph']['objects']),'objects_after':len(after['graph']['objects']),
                'edges_before':len(before['graph']['edges']),'edges_after':len(after['graph']['edges']),
                'semantic_graph_exact_except_three_id_insertions':True,'new_references':hits,
                'new_inflated_sha256':hashlib.sha256(new).hexdigest(),
                'known_registration_consistent':True,'all_possible_registration_rules_proven':False,
                'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    import argparse
    import json
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('source',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=experiment(a.reader_source,a.source,a.target,a.candidate)
    a.result.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('byte_growth','objects_before','objects_after','edges_before','edges_after','known_registration_consistent')},indent=2))
