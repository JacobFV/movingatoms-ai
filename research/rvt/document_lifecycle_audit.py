"""Read-only inventory of decoded document fields; names are evidence, not semantics."""
import argparse, hashlib, json, subprocess, tempfile, zlib
from pathlib import Path
import olefile
from codec import decode
from save_candidate import unpack_global
from new_element_registration import semantic_graph

TERMS=('bbox','bound','extent','outline','spatial','cache','level','type','cell')
def names(value,path=''):
    if isinstance(value,dict):
        for key,item in value.items():
            current=path+'.'+key
            if any(word in key.lower() for word in TERMS):yield current
            yield from names(item,current)
    elif isinstance(value,list):
        for item in value:yield from names(item,path+'[]')
def ids(value,path=''):
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='m_id64':yield path+'.'+key,item
            yield from ids(item,path+'.'+key)
    elif isinstance(value,list):
        for i,item in enumerate(value):yield from ids(item,path+f'[{i}]')
def main(source,candidate,probe):
    graphs=[];files=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for path in (source,candidate):
            with olefile.OleFileIO(path) as f:
                schema=zlib.decompress(decode(f.openstream('Formats/Latest').read()),31)
                raw=unpack_global(decode(f.openstream('Global/Latest').read()))[0]
            assert raw[-4:]==bytes(4)
            (tmp/'schema').write_bytes(schema);(tmp/'body').write_bytes(raw[:-4])
            graph=json.loads(subprocess.check_output([str(probe),'decode',str(tmp/'schema'),str(tmp/'body')]))['graph']
            assert graph['consumed_bytes']==len(raw)-4
            graphs.append(graph);files.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'graph_bytes':len(raw)-4,'objects':len(graph['objects']),'complete_decode':True})
    original,current=map(semantic_graph,graphs)
    assert len(original['objects'])==len(current['objects'])
    changes=[{'index':i,'class':a['class_name'],'changed_fields':[k for k in a['fields'] if a['fields'][k]!=b['fields'].get(k)]}for i,(a,b)in enumerate(zip(original['objects'],current['objects']))if a!=b]
    inventory=[];references=[]
    for i,obj in enumerate(original['objects']):
        fields=sorted(set(names(obj['fields'])))
        if fields or any(t in obj['class_name'].lower() for t in TERMS):
            inventory.append({'index':i,'class':obj['class_name'],'matching_field_paths':fields,'field_names':list(obj['fields']),'fields_sha256':hashlib.sha256(json.dumps(obj['fields'],sort_keys=True).encode()).hexdigest()})
        references.extend({'index':i,'class':obj['class_name'],'path':p}for p,v in ids(obj['fields'])if v==20826)
    incoming_path=Path(__file__).parent/'local/wall-element-incoming.json'
    incoming=json.loads(incoming_path.read_bytes())
    return {'files':files,'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'global_semantic_changes':changes,'global_source_wall_references':references,'named_field_inventory':inventory,'source_record_incoming_references':incoming['hits'],'incoming_scan_sha256':hashlib.sha256(incoming_path.read_bytes()).hexdigest(),'incoming_scan_limits':{k:incoming['summary'][k]for k in ('unsupported_graph_records','refused_graph_classes','refused_graph_ids','skipped_embedded_content_groups')},'limits':['Field-name inspection cannot establish absence of an encoded or differently named spatial index.','Complete Global graph decode is not complete document semantic understanding.','Preserved room topology and view overrides are existing source-specific dependencies, not registrations every new wall must inherit.','No Autodesk open, regeneration, save, selection, or spatial-query acceptance tested.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--probe',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    a.result.write_text(json.dumps(main(a.source,a.candidate,a.probe),indent=2)+'\n')
