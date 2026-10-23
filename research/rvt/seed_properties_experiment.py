"""Saved own-schema metadata control; no native application acceptance claim."""
import argparse,hashlib,json,subprocess,uuid
from pathlib import Path
from element_properties_probe import build
from element_properties import declarations_for
from element_properties_storage import SCHEMA_GUID,FIELD_NAMES,schema_definition,metadata_values,owner_bodies,register_schema_and_owner
from new_element_registration import semantic_graph
from new_element_experiment import references
from seed_record_candidate import make
from seed_metadata_audit import run as metadata_audit,streams
from seed_save_context import SOURCE_SHA
from save_candidate import unpack_global
from codec import decode as unpage
from schema_probe import REV
from wall_batch_experiment import code_snapshot,publish_checked
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def sha(value):return hashlib.sha256(value).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def verify_saved(actual,request):
    records=actual['records'];ident=request['id']
    if len(records)!=3 or {r['channel']for r in records}!={101,102,103}:raise ValueError('saved channel inventory differs')
    catalog=actual['summary']['extensible_storage_catalog']
    if set(catalog['schemas'])!={SCHEMA_GUID} or catalog['schemas'][SCHEMA_GUID]['raw_metadata']!=schema_definition():raise ValueError('saved dynamic schema differs')
    positives=set()
    for record in records:
        graph=record['graph']
        if record['identity']['element_id']!=ident or record['source']['stream']!='Partitions/1':raise ValueError('saved identity/routing differs')
        if not graph or graph['consumed_bytes']!=record['source']['body_bytes']:raise ValueError('incomplete saved graph')
        positives.update(v['id']for o in graph['objects']for v in references(o['fields'])if v['id']>0)
    if positives!={ident}:raise ValueError('unexpected positive reference')
    graph=next(r['graph']for r in records if r['channel']==102)
    root=graph['objects'][0]
    if root['class_name']!='DataStorage' or root['fields']['m_id']['m_id']['m_id64']!=ident or root['fields']['m_name']!=request['name']:raise ValueError('saved owner identity/name differs')
    entities=[o['fields']for o in graph['objects']if o['class_name']=='ExtensibleStorageEntity']
    if len(entities)!=1 or entities[0]['schema_guid']!=SCHEMA_GUID:raise ValueError('saved entity differs')
    fields=entities[0]['fields']
    values=tuple(f['raw_value']for f in fields)
    expected=metadata_values(request['application_id'],request['name'],request['properties'])
    if values!=expected or json.loads(values[2])!=request['properties']:raise ValueError('saved metadata values differ')
    return {'new_element_id':ident,'all_three_saved_channels_complete':True,'dynamic_catalog_discovered_from_saved_file':True,
            'own_schema_metadata_exact':True,'application_id_name_properties_exact':True,'positive_reference_ids':sorted(positives)}

def run(source,output,reader,target,writer,*,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit save/registration/lifecycle hypotheses acknowledgment required')
    source,output,reader,target,writer=(p.resolve()for p in(source,output,reader,target,writer))
    if output.exists():raise FileExistsError(output)
    if sha(source.read_bytes())!=SOURCE_SHA:raise ValueError('pinned minimal seed required')
    code=code_snapshot();writer_hash=sha(writer.read_bytes())
    context_bytes=(HERE/'results/seed_save_context.json').read_bytes()
    output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','source_sha256':SOURCE_SHA,'reader_revision':REV,'autodesk_acceptance':'not_tested','complete_save_transaction':False,'code_sha256':code,'writer_sha256':writer_hash,'context_sha256':sha(context_bytes)}
    write(output/'run.json',report)
    try:
        probe=build(reader,target,output)
        request={'id':2746,'application_id':'movingatoms:item-42','name':'Application wall 😀',
                 'properties':{'dimensions':{'height_metres':3.2},'enabled':True,'labels':['A','😀'],'optional':None}}
        write(output/'request.json',request)
        old=streams(source);schema=zlib.decompress(unpage(old['Formats/Latest']),31)
        original=unpack_global(unpage(old['Global/Latest']))[0]
        schema_path=output/'schema.bin';schema_path.write_bytes(schema)
        global_path=output/'source-global.bin';global_path.write_bytes(original)
        def invoke(*args):return json.loads(subprocess.check_output([str(probe),*map(str,args)]))
        before=invoke('esglobal',schema_path,global_path)
        registered,expected,changes=register_schema_and_owner(original,before['graph'],before['declarations'],request['id'])
        names={'DataStorage','ElementHeader','SerializedDummy','CellList','ESEntityCell','ElementParents'}
        declarations=declarations_for(before['declarations'],[{'objects':[{'class_tag':c['tag']}for c in before['declarations']if c['name']in names]}])
        bodies=owner_bodies(declarations,request['id'],request['application_id'],request['name'],request['properties'])
        evidence={'source_sha256':SOURCE_SHA,'source_global_sha256':sha(original),'registered_global_sha256':sha(registered),
                  'method':'Own fresh scalar string schema plus schema/entity-cell owner tracking; saved dirty=0 hypothesis','changes':changes}
        context=json.loads(context_bytes)
        episode=str(uuid.uuid5(uuid.UUID(SCHEMA_GUID),json.dumps(request,sort_keys=True)))
        plan=make(source,output/'patches',[{'id':request['id'],'bodies':bodies}],context,registered,evidence,episode_guid=episode,timestamp=1792627200,acknowledge_hypotheses=True)
        candidate=output/'candidate.rvt'
        (output/'transport.json').write_bytes(subprocess.check_output([str(writer),'patch',str(source),str(candidate),str(output/'patches/manifest.json')]))
        (output/'transport-verify.json').write_bytes(subprocess.check_output([str(writer),'verify',str(candidate)]))
        metadata=metadata_audit(source,candidate)
        if metadata['table']['new_ids']!=[request['id']]:raise ValueError('unexpected saved allocation')
        write(output/'metadata.json',metadata)
        saved_global=unpack_global(unpage(streams(candidate)['Global/Latest']))[0]
        global_path=output/'saved-global.bin';global_path.write_bytes(saved_global)
        after=invoke('esglobal',schema_path,global_path)
        if saved_global!=registered or semantic_graph(after['graph'])!=semantic_graph(expected):raise ValueError('saved Global semantics differ')
        actual=invoke('saved',candidate,request['id']);write(output/'saved-native.json',actual)
        checked=verify_saved(actual,request)
        for record in actual['records']:
            ch=str(record['channel'])
            if metadata['body_sha256'][ch][str(request['id'])]!=plan['records'][0]['body_sha256'][ch]:raise ValueError('saved body hash differs')
        checked.update(saved_global_exact=True,unrelated_global_fields_preserved=True,candidate_sha256=sha(candidate.read_bytes()))
        write(output/'native.json',checked)
        if code_snapshot()!=code or sha(writer.read_bytes())!=writer_hash or sha(source.read_bytes())!=SOURCE_SHA or (HERE/'results/seed_save_context.json').read_bytes()!=context_bytes:raise ValueError('code/tool/source/evidence changed during verification')
        publish_checked(candidate,output/'verified-candidate.rvt',[metadata,checked])
        report.update(status='verified_research_candidate',candidate_sha256=sha(candidate.read_bytes()),new_element_id=request['id'],
           all_source_rows_and_partition_preserved=True,checks=checked,writer_sha256=sha(writer.read_bytes()),probe_sha256=sha(probe.read_bytes()),
           validation_reports={n:sha((output/n).read_bytes())for n in('metadata.json','native.json','saved-native.json','transport.json','transport-verify.json')},
           limitations=['Unsigned partition and ancillary save policies remain hypotheses.','Own-only DataStorage and fresh schema registration are not native-application validated.','Separate metadata owner; no inferred wall attachment.'])
        write(output/'run.json',report);return report
    except Exception as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}');write(output/'run.json',report);raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reader',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--writer',type=Path,default=ROOT/'processing/rvt-native/target/release/ma-rvt-native')
    p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args()
    print(json.dumps(run(a.source,a.output,a.reader,a.target,a.writer,acknowledge_hypotheses=a.acknowledge_hypotheses),indent=2))
