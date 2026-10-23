"""Generic experimental append of caller-supplied new records to the pinned seed.

No class construction or registration is inferred here. Separate independent
schema decoding and lifecycle audits remain required before any acceptance claim.
"""
import argparse,hashlib,json,uuid,zlib
from pathlib import Path
import olefile
from codec import decode as unpage
import element_table,save_history,save_increments,basic_file_info_codec
from save_candidate import unpack_global,repack_global,advance_regular_ancillary_revisions
from new_element import allocate_identity
from partition_builder import build_partition
from partition_objects import Record,validate as validate_objects
from partition_segments import encode as encode_partition,decode as decode_partition
from seed_save_context import SOURCE_SHA,allocation_plan,patch_seed_contents,patch_seed_timestamp

def sha(data):return hashlib.sha256(data).hexdigest()

def checked_records(records,first_id):
    if not isinstance(records,list) or not 1<=len(records)<=100:raise ValueError('requires 1..100 complete records')
    output=[]
    for offset,record in enumerate(records):
        if isinstance(record,dict) and set(record)=={'element_id','channels'}:
            record={'id':record['element_id'],'bodies':record['channels']}
        if not isinstance(record,dict) or set(record)!={'id','bodies'} or type(record['id'])is not int or record['id']!=first_id+offset:
            raise ValueError('record IDs must follow stored allocator in order')
        bodies=record['bodies']
        if not isinstance(bodies,dict) or set(bodies)!={101,102,103} or any(type(ch)is not int for ch in bodies):raise ValueError('requires exactly channels101/102/103')
        if any(type(body)is not bytes or len(body)<2 for body in bodies.values()):raise ValueError('nonempty binary object bodies required')
        output.append({'id':record['id'],'bodies':dict(bodies)})
    return output

def check_registration(original,registered,evidence):
    if type(registered)is not bytes or not registered.endswith(bytes(4)):raise ValueError('complete inflated Global bytes required')
    required={'source_sha256','source_global_sha256','registered_global_sha256','method','changes'}
    if not isinstance(evidence,dict) or not required<=set(evidence):raise ValueError('explicit registration evidence required')
    if evidence['source_sha256']!=SOURCE_SHA or evidence['source_global_sha256']!=sha(original) or evidence['registered_global_sha256']!=sha(registered):raise ValueError('registration evidence hash binding differs')
    if not isinstance(evidence['method'],str) or not evidence['method'].strip() or not isinstance(evidence['changes'],list):raise ValueError('registration policy must be explicit')
    if original!=registered and not evidence['changes']:raise ValueError('changed Global requires declared registration changes')
    return evidence

def make(source,dest,records,save_context,registered_global,registration_evidence,*,episode_guid,timestamp,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit unsigned/registration/lifecycle hypothesis acknowledgment required')
    source=Path(source);dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    if sha(source.read_bytes())!=SOURCE_SHA or save_context['source_sha256']!=SOURCE_SHA:raise ValueError('requires exact licensed minimal seed')
    episode=uuid.UUID(episode_guid)
    names=['Global/History','Global/ElemTable','Global/DocumentIncrementTable','Contents','BasicFileInfo','Global/Latest','ProjectInformation']
    with olefile.OleFileIO(source)as f:
        stored={n:f.openstream(n).read()for n in names}
        schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        if f.exists('Partitions/1'):raise ValueError('partition1 already exists')
    if sha(schema)!=save_context['schema_sha256']:raise ValueError('seed schema evidence differs')
    logical={n:unpage(v)for n,v in stored.items()if n not in ('BasicFileInfo','ProjectInformation')}
    history=save_history.decode(unpack_global(logical['Global/History'])[0]);table=element_table.decode(unpack_global(logical['Global/ElemTable'])[0],8)
    tag,fields=save_increments.decode(unpack_global(logical['Global/DocumentIncrementTable'])[0])
    if history.next_sequence!=1 or table.last_id!=2745 or len(fields['m_increments'])!=1:raise ValueError('unmeasured seed allocation state')
    records=checked_records(records,table.last_id+1)
    registration=check_registration(unpack_global(logical['Global/Latest'])[0],registered_global,registration_evidence)
    allocation=allocation_plan(table,history,fields,len(records),timestamp,str(episode))
    if allocation['partition_ordinal_hypothesis']!=1:raise ValueError('unexpected append partition')
    newtable=table
    for record in records:
        ident,newtable=allocate_identity(newtable,history)
        if ident!=record['id']:raise ValueError('allocator disagreement')
    revised=allocation['increment_fields']
    for key in ('m_increments','m_localIncrements'):
        revised[key][-1]['m_basicFileInfoStreamRevision']+=1
        revised[key][-1]['m_comment']='Unsigned minimal-seed record append; caller-declared registration and lifecycle hypotheses'
    revised=advance_regular_ancillary_revisions(fields,revised)
    revisions={n:revised['m_increments'][-1][f'm_{n}StreamRevision']for n in save_increments.REVISIONS}
    project,xml_evidence=patch_seed_timestamp(stored['ProjectInformation'],fields['m_increments'][-1]['m_atimeStamp']['m_lsb'],timestamp)
    partition=encode_partition(build_partition(0x37b,{ch:tuple(Record(r['id'],r['bodies'][ch])for r in records)for ch in (101,102,103)},8,allow_unsigned_nonempty=True))
    check=decode_partition(partition)
    if len(check.segments)!=1 or check.segments[0].count!=len(records):raise ValueError('partition framing roundtrip differs')
    decoded=validate_objects(check.segments[0],8)
    for ch in (101,102,103):
        if [(r.element_id,r.body)for r in decoded[ch][:-1]]!=[(r['id'],r['bodies'][ch])for r in records]:raise ValueError('partition body roundtrip differs')
    payloads={
      'Global/History':repack_global(logical['Global/History'],save_history.encode(save_history.prepend_episode(history,episode.bytes_le))),
      'Global/ElemTable':repack_global(logical['Global/ElemTable'],element_table.encode(newtable)),
      'Global/DocumentIncrementTable':repack_global(logical['Global/DocumentIncrementTable'],save_increments.encode(tag,revised)),
      'Contents':patch_seed_contents(logical['Contents'],save_context,revisions),
      'BasicFileInfo':basic_file_info_codec.encode(basic_file_info_codec.decode(stored['BasicFileInfo']),allocation['new_major_version'],str(episode)),
      'Global/Latest':repack_global(logical['Global/Latest'],registered_global),'ProjectInformation':project}
    if registered_global==unpack_global(logical['Global/Latest'])[0]:
        del payloads['Global/Latest']
    plan={'source_sha256':SOURCE_SHA,'schema_sha256':sha(schema),'expected_new_ids':[r['id']for r in records],
      'new_partition':'Partitions/1','new_episode':1,'new_episode_guid':str(episode),'timestamp':timestamp,
      'records':[{'id':r['id'],'body_sha256':{str(ch):sha(body)for ch,body in r['bodies'].items()}}for r in records],
      'registration_evidence':registration,'global_stored_bytes_preserved': 'Global/Latest' not in payloads,'project_information_timestamp':xml_evidence,
      'partition_payload_sha256':sha(partition),'source_rows':len(table.rows),'new_rows':len(newtable.rows),
      'all_source_rows_preserved':newtable.rows[:-len(records)]==table.rows,
      'autodesk_acceptance':'not_tested','production_native_export':False,'complete_save_transaction':False,
      'hypotheses':['Unsigned append partition acceptance.','Caller-declared registration is sufficient.','Selected ancillary revision and timestamp policies.','No native regeneration or signature acceptance established.'],
      'required_external_validation':['Decode actual saved candidate bodies independently; verify classes, identities, all outgoing references.','Verify supplied Global registration independently against measured schema and intended classes.']}
    dest.mkdir(parents=True,exist_ok=False);patches=[]
    for name,payload in payloads.items():
        filename=name.replace('/','-')+'.bin';(dest/filename).write_bytes(payload)
        patches.append({'stream':name,'expected_stored_sha256':sha(stored[name]),'new_payload_file':filename})
    (dest/'partition.bin').write_bytes(partition)
    (dest/'manifest.json').write_text(json.dumps({'input_sha256':SOURCE_SHA,'patches':patches,'creates':[{'stream':'Partitions/1','expected_absent':True,'new_payload_file':'partition.bin'}]},indent=2)+'\n')
    (dest/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');return plan

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('dest',type=Path);p.add_argument('--request',type=Path,required=True);p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args()
    request=json.loads(a.request.read_bytes());base=a.request.parent
    records=[{'id':r['id'],'bodies':{int(ch):(base/path).read_bytes()for ch,path in r['body_files'].items()}}for r in request['records']]
    evidence=json.loads((base/request['registration_evidence_file']).read_bytes());context=json.loads((Path(__file__).parent/'results/seed_save_context.json').read_bytes())
    result=make(a.source,a.dest,records,context,(base/request['registered_global_file']).read_bytes(),evidence,episode_guid=request['episode_guid'],timestamp=request['timestamp'],acknowledge_hypotheses=a.acknowledge_hypotheses)
    print(json.dumps(result,indent=2))
