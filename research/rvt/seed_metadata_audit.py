"""Read actual seed/candidate streams; builder plan is an optional cross-check."""
import argparse,hashlib,io,json,struct,zipfile,zlib
from datetime import datetime
from pathlib import Path
import olefile
from codec import decode as unpage
from wall_batch_metadata_audit import audit_history,audit_table,inflate_global
from save_increments import decode as decode_increments,REVISIONS
from partition_segments import decode as decode_partition
from partition_objects import validate as validate_objects
from basic_file_info_codec import decode as decode_basic,encode as encode_basic
from project_information_codec import parse as parse_project

SOURCE_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'
def sha(b):return hashlib.sha256(b).hexdigest()
def streams(path):
    with olefile.OleFileIO(path)as f:return {'/'.join(n):f.openstream(n).read()for n in f.listdir()}
def inflate_contents(logical):
    if len(logical)<101 or logical[91:95]!=b'\x1f\x8b\x08\0':raise ValueError('seed Contents framing differs')
    d=zlib.decompressobj(31);raw=d.decompress(logical[91:])
    if not d.eof or d.unconsumed_tail or d.unused_data!=b'\0':raise ValueError('seed Contents suffix differs')
    return raw

def audit_streams(old,new,evidence):
    history=audit_history(inflate_global(old['Global/History']),inflate_global(new['Global/History']))
    table=audit_table(inflate_global(old['Global/ElemTable']),inflate_global(new['Global/ElemTable']),history['creation_episode'])
    ids=table['new_ids'];count=len(ids)
    oldtag,prior=decode_increments(inflate_global(old['Global/DocumentIncrementTable']));newtag,current=decode_increments(inflate_global(new['Global/DocumentIncrementTable']))
    if oldtag!=newtag or prior['m_permutation'] or current['m_permutation']:raise ValueError('increment framing/permutation differs')
    if current['m_increments']!=current['m_localIncrements']:raise ValueError('increment arrays disagree')
    for name in ('m_increments','m_localIncrements'):
        if len(current[name])!=len(prior[name])+1 or current[name][:-1]!=prior[name]:raise ValueError('old increment rows changed')
    before=prior['m_increments'][-1];after=current['m_increments'][-1]
    if (after['m_greatest']['m_id']!=history['creation_episode'] or after['m_totalEpisodes']!=history['new_history_count'] or after['m_majorVersion']!=before['m_majorVersion']+1 or after['m_overwrite']):raise ValueError('new increment episode/version/overwrite differs')
    if after['m_totalElements']!=count or after['m_incrementVersions']!=[{'m_causedByIncrementNumber':-1,'m_totalElements':count}]:raise ValueError('increment element counts differ from table')
    if before['m_atimeStamp']['m_msb'] or after['m_atimeStamp']['m_msb'] or not after['m_atimeStamp']['m_lsb']>before['m_atimeStamp']['m_lsb']:raise ValueError('increment timestamp does not advance')
    deltas={}
    for name in REVISIONS:
        key=f'm_{name}StreamRevision';deltas[name]=after[key]-before[key]
        if deltas[name]!=(0 if name in ('preview','formats','partAtom')else 1):raise ValueError('selected revision policy differs: '+name)
    partition_name='Partitions/'+str(len(prior['m_increments']))
    if set(new)-set(old)!={partition_name} or set(old)-set(new):raise ValueError('stream inventory differs')
    changed={k for k in old if old[k]!=new[k]}
    expected={'Global/Latest','Global/History','Global/ElemTable','Global/DocumentIncrementTable','Contents','BasicFileInfo','ProjectInformation'}
    if changed!=expected:raise ValueError('unexpected changed source streams')
    partition=decode_partition(unpage(new[partition_name]))
    if len(partition.segments)!=1 or partition.segments[0].guid is not None or partition.segments[0].count!=count:raise ValueError('partition groups/count differ')
    records=validate_objects(partition.segments[0],8)
    if set(records)!={101,102,103}:raise ValueError('partition channel inventory differs')
    hashes={}
    for channel,values in records.items():
        if [v.element_id for v in values]!=ids+[2**64-1] or values[-1].body:raise ValueError('partition IDs/sentinel differ')
        hashes[str(channel)]={str(v.element_id):sha(v.body)for v in values[:-1]}
    b0=decode_basic(old['BasicFileInfo']);b1=decode_basic(new['BasicFileInfo'])
    if b0.increments!=len(prior['m_increments']) or b1.increments!=after['m_majorVersion'] or b1.guid!=history['new_episode_guid']:raise ValueError('BasicFileInfo identity disagreement')
    if encode_basic(b0,increments=b1.increments,document_guid=b1.guid)!=new['BasicFileInfo']:raise ValueError('unrelated BasicFileInfo bytes changed')
    old_logical=unpage(old['Contents']);new_logical=unpage(new['Contents']);oldbody=inflate_contents(old_logical);newbody=inflate_contents(new_logical)
    if sha(old_logical)!=evidence['contents_logical_sha256'] or sha(oldbody)!=evidence['contents_inflated_sha256']:raise ValueError('Contents evidence differs from actual source')
    expected_body=bytearray(oldbody);keys=set()
    for span in evidence['contents_root']['field_spans']:
        key=span['name']
        if key.startswith('m_')and key.endswith('StreamRevision'):
            if span['end']-span['start']!=4 or key in keys:raise ValueError('invalid Contents revision spans')
            keys.add(key)
            if struct.unpack_from('<i',oldbody,span['start'])[0]!=before[key]:raise ValueError('source Contents revision mismatch')
            struct.pack_into('<i',expected_body,span['start'],after[key])
    if keys!={f'm_{n}StreamRevision'for n in REVISIONS if n!='formats'}:raise ValueError('incomplete Contents revision evidence')
    header=bytearray(old_logical[:91]);struct.pack_into('<i',header,87,after['m_formatsStreamRevision'])
    if newbody!=expected_body or new_logical[:91]!=header:raise ValueError('Contents revision/opaque bytes differ')
    oldxml,oldstamp,*_=parse_project(old['ProjectInformation']);newxml,newstamp,*_=parse_project(new['ProjectInformation'])
    def seconds(stamp):return int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp())
    if before['m_atimeStamp']['m_lsb']-seconds(oldstamp)!=10800 or after['m_atimeStamp']['m_lsb']-seconds(newstamp)!=10800:raise ValueError('seed XML offset differs')
    if oldxml.replace(oldstamp.encode(),newstamp.encode())!=newxml:raise ValueError('unrelated XML changed')
    zip_fields=('filename','date_time','compress_type','comment','extra','create_system','create_version','extract_version','flag_bits','volume','internal_attr','external_attr')
    with zipfile.ZipFile(io.BytesIO(old['ProjectInformation']))as a,zipfile.ZipFile(io.BytesIO(new['ProjectInformation']))as b:
        if len(a.infolist())!=1 or len(b.infolist())!=1:raise ValueError('ZIP entry count differs')
        if any(getattr(a.infolist()[0],k)!=getattr(b.infolist()[0],k)for k in zip_fields)or a.comment!=b.comment:raise ValueError('ZIP entry metadata changed')
    return {'history':history,'table':table,'new_partition':partition_name,'new_increment_total_elements':count,'body_sha256':hashes,'revision_deltas':deltas,'contents_all_revisions_match':True,'contents_zero_suffix_preserved':True,'basic_identity_and_other_bytes_verified':True,'project_information_offset_seconds':10800,'project_information_other_xml_and_zip_metadata_preserved':True,'all_old_increment_rows_preserved':True,'original_partition_streams_preserved':True,'changed_existing_streams':sorted(changed)}

def run(source,candidate,plan=None):
    if sha(source.read_bytes())!=SOURCE_SHA:raise ValueError('requires pinned licensed seed')
    evidence=json.loads((Path(__file__).parent/'results/seed_save_context.json').read_bytes())
    report=audit_streams(streams(source),streams(candidate),evidence)
    if plan is not None:
        if plan['source_sha256']!=SOURCE_SHA or plan['expected_new_ids']!=report['table']['new_ids'] or plan['new_episode_guid']!=report['history']['new_episode_guid'] or plan['new_partition']!=report['new_partition']:raise ValueError('plan metadata differs from actual file')
        for channel,bodyhash in plan['level_body_sha256'].items():
            if report['body_sha256'][channel][str(plan['new_level_id'])]!=bodyhash:raise ValueError('level plan body hash differs')
        for wall in plan['walls']:
            for channel,bodyhash in wall['body_sha256'].items():
                if report['body_sha256'][channel][str(wall['id'])]!=bodyhash:raise ValueError('wall plan body hash differs')
    return {'source_sha256':SOURCE_SHA,'candidate_sha256':sha(candidate.read_bytes()),'builder_plan_used_only_as_optional_crosscheck':plan is not None,**report,'limits':['Selected append/revision/registration policies remain hypotheses, not Autodesk acceptance.','Global registrations and decoded native element graphs are verified by a separate audit.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--plan',type=Path);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.source,a.candidate,json.loads(a.plan.read_bytes())if a.plan else None)
    with a.result.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
