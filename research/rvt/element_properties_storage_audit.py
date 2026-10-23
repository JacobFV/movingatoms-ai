"""Fresh ES schema registration and own metadata owner, verified on seed and Core."""
import argparse,hashlib,json,subprocess,zlib
from pathlib import Path
import olefile
from codec import decode as unpage
from element_table import decode as table_decode
from element_properties import declarations_for
from element_properties_probe import build
from element_properties_storage import register_schema_and_owner,owner_bodies,metadata_values,SCHEMA_GUID,SCHEMA_NAME,schema_definition
from new_element_registration import semantic_graph
from new_element_experiment import references
from schema_probe import REV

FIXTURES=[('core2024.rvt','c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'),
          ('minimal_seed-Project.rvt','674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe')]


def run(source,target,directory):
    binary=build(source,target,directory);reports=[]
    properties={'dimensions':{'height_metres':3.2},'enabled':True,'labels':['A','😀'],'optional':None}
    app_id='app:item-42';name='Example wall';values=metadata_values(app_id,name,properties)
    for filename,sha in FIXTURES:
        path=directory/filename
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('fixture mismatch')
        base=directory/('element-properties-es-'+path.stem)
        with olefile.OleFileIO(path) as file:
            for suffix,stream,skip in [('schema','Formats/Latest',0),('global','Global/Latest',8),('table','Global/ElemTable',8)]:
                raw=unpage(file.openstream(stream).read())[skip:];d=zlib.decompressobj(31);data=d.decompress(raw)
                if not d.eof or d.unconsumed_tail:raise ValueError('invalid global gzip')
                Path(str(base)+'.'+suffix).write_bytes(data)
        schema_path=Path(str(base)+'.schema');global_path=Path(str(base)+'.global')
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        original=probe('esglobal',schema_path,global_path)
        table=table_decode(Path(str(base)+'.table').read_bytes(),8);owner_id=table.last_id+1
        if owner_id in [table.current(row)for row in table.rows]:raise ValueError('owner ID not fresh')
        changed,expected,changes=register_schema_and_owner(global_path.read_bytes(),original['graph'],original['declarations'],owner_id)
        changed_path=Path(str(base)+'-changed.global');changed_path.write_bytes(changed)
        after=probe('esglobal',schema_path,changed_path)
        if semantic_graph(after['graph'])!=semantic_graph(expected):raise ValueError('unrelated global graph semantics changed')
        existing={k:v for k,v in after['catalog']['schemas'].items()if k!=SCHEMA_GUID}
        if existing!=original['catalog']['schemas']:raise ValueError('existing schema definitions changed')
        own=after['catalog']['schemas'][SCHEMA_GUID]
        if own['raw_metadata']!=schema_definition():raise ValueError('new schema independently differs')
        cat=Path(str(base)+'-catalog.json');cat.write_text(json.dumps(after['catalog']))
        names=('DataStorage','ElementHeader','SerializedDummy','CellList','ESEntityCell','ElementParents')
        tags=[c['tag']for c in original['declarations']if c['name']in names]
        declarations=declarations_for(original['declarations'],[{'objects':[{'class_tag':t}for t in tags]}])
        bodies=owner_bodies(declarations,owner_id,app_id,name,properties);channels={}
        for seq,body in bodies.items():
            out=Path(str(base)+f'-{seq}.bin');out.write_bytes(body)
            graph=probe('esdecode',schema_path,out,cat)
            if graph['consumed_bytes']!=len(body):raise ValueError('entity body not fully consumed')
            positives=[v['id']for o in graph['objects']for v in references(o['fields'])if v['id']>0]
            if any(v!=owner_id for v in positives):raise ValueError('unexpected owner dependency')
            if seq==102:
                entities=[o for o in graph['objects']if o['class_name']=='ExtensibleStorageEntity']
                if len(entities)!=1 or entities[0]['fields']['schema_guid']!=SCHEMA_GUID:raise ValueError('wrong entity schema')
                decoded_values=tuple(f['raw_value']for f in entities[0]['fields']['fields'])
                if decoded_values!=values or json.loads(decoded_values[2])!=properties:raise ValueError('application properties differ')
            channels[str(seq)]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),
                'complete_graph_objects':len(graph['objects']),'complete_body_consumed':True,
                'positive_reference_ids':positives}
        reports.append({'file':filename,'source_sha256':sha,'reader_commit':REV,'allocated_owner_id':owner_id,
           'schemas_before':len(original['catalog']['schemas']),'schemas_after':len(after['catalog']['schemas']),
           'source_registration_objects_reconstructed_exactly':True,'only_intended_global_fields_changed':True,
           'existing_schemas_preserved':True,'owned_catalog_discovered_independently':True,'global_changes':changes,
           'global_before_sha256':hashlib.sha256(global_path.read_bytes()).hexdigest(),
           'global_after_sha256':hashlib.sha256(changed).hexdigest(),'channels':channels,
           'application_id':app_id,'name':name,'properties':properties,'independent_entity_values_exact':True})
    return {'schema_guid':SCHEMA_GUID,'schema_name':SCHEMA_NAME,'schema_metadata':schema_definition(),
       'fixtures':reports,'hypotheses':['Appending schema/tracking maps and retaining saved dirty=0 is inferred from measured layouts.',
          'New DataStorage has only the own application entity, without inherited vendor identity/exchange entities.',
          'No complete save or native acceptance is established by global/catalog/entity decoding.'],
       'complete_native_save':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.target,a.directory),indent=2))
