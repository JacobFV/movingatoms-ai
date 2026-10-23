"""Independent decoded controls for multiple owners and attached own entities."""
import argparse,hashlib,json,subprocess,zlib
from copy import deepcopy
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode as partition_decode
from partition_objects import validate
from element_properties_probe import build
from element_properties import normalized_objects
from element_properties_storage import SCHEMA_GUID,metadata_values
from element_properties_storage_batch import attach,register_schema_and_owners
from new_element_registration import semantic_graph
from save_candidate import unpack_global
from seed_save_context import SOURCE_SHA
from schema_probe import REV

def run(reader,target,directory):
    probe=build(reader,target,directory)
    def invoke(*args):return json.loads(subprocess.check_output([str(probe),*map(str,args)]))
    seed=directory/'minimal_seed-Project.rvt';base=directory/'element-properties-batch'
    if hashlib.sha256(seed.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('seed hash differs')
    with olefile.OleFileIO(seed)as f:
        schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        original=unpack_global(unpage(f.openstream('Global/Latest').read()))[0]
    schema_path=Path(str(base)+'.schema');schema_path.write_bytes(schema)
    global_path=Path(str(base)+'.global');global_path.write_bytes(original)
    source=invoke('esglobal',schema_path,global_path)
    changed,expected,changes=register_schema_and_owners(original,source['graph'],source['declarations'],[2746,2747])
    global_path.write_bytes(changed);after=invoke('esglobal',schema_path,global_path)
    if semantic_graph(after['graph'])!=semantic_graph(expected):raise ValueError('batch registration semantics differ')
    catalog_path=Path(str(base)+'.catalog.json');catalog_path.write_text(json.dumps(after['catalog']))
    fixtures=[('DirectShape',directory/'seed-directshape-run-v3/verified-candidate.rvt',2746),('SWall',directory/'core2024.rvt',20826)]
    trials=[]
    for name,path,ident in fixtures:
        required={'DirectShape':'a971271cbc5eac80a471cd9498e5ae1dbe70d9baecd3e25a4145c28b5f912623','SWall':'c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'}
        if hashlib.sha256(path.read_bytes()).hexdigest()!=required[name]:raise ValueError('attachment source hash differs')
        saved=invoke('saved',path,ident);record=next(r for r in saved['records']if r['channel']==102)
        with olefile.OleFileIO(path)as f:
            partition=partition_decode(unpage(f.openstream(record['source']['stream']).read()))
            body=next(r.body for r in validate(partition.segments[0],8)[102]if r.element_id==ident)
        if hashlib.sha256(body).hexdigest()!=record['source']['body_sha256']:raise ValueError('source body differs')
        props={'nested':{'height':3.2},'tags':['test','😀'],'enabled':True}
        args=('movingatoms:attached-'+str(ident),name+' attached',props)
        newbody,report=attach(record['graph'],source['declarations'],body,*args,acknowledge_hypotheses=True)
        body_path=Path(str(base)+'-'+name+'.bin');body_path.write_bytes(newbody)
        decoded=invoke('esdecode',schema_path,body_path,catalog_path)
        entities=[o for o in decoded['objects']if o['class_name']=='ExtensibleStorageEntity']
        if len(entities)!=1 or tuple(f['raw_value']for f in entities[0]['fields']['fields'])!=metadata_values(*args):raise ValueError('attached entity values differ')
        recovered=deepcopy(decoded)
        recovered['objects']=[o for o in recovered['objects']if o['class_name']not in ('ExtensibleStorageEntity','ESEntityCell')]
        if report['original_cell_list_was_null']:
            recovered['objects']=[o for o in recovered['objects']if o['class_name']!='CellList']
            recovered['objects'][0]['fields']['m_cellList']=deepcopy(record['graph']['objects'][0]['fields']['m_cellList'])
        else:
            next(o for o in recovered['objects']if o['class_name']=='CellList')['fields']['m_cells'].pop()
        if normalized_objects(recovered)!=normalized_objects(record['graph']):raise ValueError('original owner/geometry fields changed')
        trials.append({'owner_class':name,'source_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_owner_id':ident,
          'source_body_sha256':hashlib.sha256(body).hexdigest(),'attached_body_sha256':hashlib.sha256(newbody).hexdigest(),
          'source_bytes':len(body),'attached_bytes':len(newbody),'source_reconstructed_exactly':True,
          'all_original_object_fields_preserved_except_cell_attachment':True,'independent_entity_values_exact':True,
          'complete_body_consumed':decoded['consumed_bytes']==len(newbody),'source_cell_list_was_null':report['original_cell_list_was_null']})
    return {'reader_revision':REV,'seed_source_sha256':SOURCE_SHA,'schema_guid':SCHEMA_GUID,'registered_owner_ids':[2746,2747],'single_schema_registered':len(after['catalog']['schemas'])==1,
      'batch_global_semantics_independently_exact':True,'global_changes':changes,'trials':trials,
      'limitations':['Attached own ES lifecycle is an unvalidated hypothesis; source wall has no measured ES entity.',
      'DirectShape control itself is a research candidate, not an Autodesk-authored2024 instance.',
      'Batch registration IDs2746/2747 are a separate seed control; Core wall20826 attachment is body-only, not registered in that seed.',
      'No complete combined document is emitted by this audit.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(run(a.reader,a.target,a.directory),indent=2))
