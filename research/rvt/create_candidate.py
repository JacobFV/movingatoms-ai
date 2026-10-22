"""Pinned fresh DataStorage append experiment; root registration is unresolved.

Constructs bounded new object bodies and coordinated known save metadata.
Unsigned acceptance and complete document registration are not established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zlib
import olefile
from codec import decode as unpage
from save_candidate import unpack_global,repack_global,append_increment,advance_regular_ancillary_revisions
import element_table
import save_history
import save_increments
import basic_file_info_codec
from save_identity import patch_contents_payload
from partition_builder import build_partition
from partition_objects import Record
from partition_segments import encode as partition_encode
from new_element import data_storage,allocate_identity
from new_element_experiment import SOURCE_SHA,EPISODE,STORAGE,NAME
from schema_probe import REV


def make(source,dest,profile,identity_evidence,*,acknowledge_hypotheses=False,registration_evidence=None,synchronize_ancillary=False):
    if synchronize_ancillary and registration_evidence is None:raise ValueError('ancillary variant requires measured registration evidence')
    if not acknowledge_hypotheses:raise ValueError('explicit acknowledgment of unsigned/registration hypotheses required')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('requires pinned core2024 fixture')
    if profile['source_sha256']!=SOURCE_SHA or profile['reader_revision']!=REV:raise ValueError('profile source/reader differs')
    matches=[r for r in identity_evidence if r['sha256']==SOURCE_SHA]
    if len(matches)!=1:raise ValueError('requires unique pinned identity evidence')
    evidence=matches[0]
    streams=['Global/History','Global/ElemTable','Global/DocumentIncrementTable','Contents','BasicFileInfo']
    with olefile.OleFileIO(source)as f:
        stored={s:f.openstream(s).read()for s in streams}
        original_global=f.openstream('Global/Latest').read()
        original_project=f.openstream('ProjectInformation').read() if synchronize_ancillary else None
        schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        if f.exists('Partitions/66'):raise ValueError('partition66 already exists')
    if hashlib.sha256(schema).hexdigest()!=profile['schema_sha256']:raise ValueError('embedded schema profile mismatch')
    logical={s:unpage(stored[s])for s in streams[:-1]}
    history=save_history.decode(unpack_global(logical[streams[0]])[0])
    table=element_table.decode(unpack_global(logical[streams[1]])[0],8)
    tag,fields=save_increments.decode(unpack_global(logical[streams[2]])[0])
    if len(fields['m_increments'])!=66 or history.next_sequence!=39 or table.last_id!=133209:
        raise ValueError('source allocation state differs')
    ident,newtable=allocate_identity(table,history)
    if ident!=133210:raise ValueError('unexpected allocation')
    newhistory=save_history.prepend_episode(history,EPISODE.bytes_le)
    bodies=data_storage(profile['declarations'],profile['catalog'],ident,NAME,STORAGE)
    partition=build_partition(0x37b,{s:(Record(ident,b),)for s,b in bodies.items()},8,allow_unsigned_nonempty=True)
    revised=append_increment(fields,39,1792627200)
    for name in ('m_increments','m_localIncrements'):
        revised[name][-1]['m_comment']='Unsigned new DataStorage; registration unresolved'
        revised[name][-1]['m_basicFileInfoStreamRevision']+=1
    if synchronize_ancillary:revised=advance_regular_ancillary_revisions(fields,revised)
    revisions={n:revised['m_increments'][-1][f'm_{n}StreamRevision']for n in save_increments.REVISIONS}
    payloads={streams[0]:repack_global(logical[streams[0]],save_history.encode(newhistory)),
              streams[1]:repack_global(logical[streams[1]],element_table.encode(newtable)),
              streams[2]:repack_global(logical[streams[2]],save_increments.encode(tag,revised)),
              'Contents':patch_contents_payload(logical['Contents'],evidence,revisions),
              'BasicFileInfo':basic_file_info_codec.encode(basic_file_info_codec.decode(stored['BasicFileInfo']),67,str(EPISODE))}
    registration_changes=[]
    if registration_evidence is not None:
        from new_element_registration import register
        registration_evidence=registration_evidence.get('source_evidence',registration_evidence)
        global_logical=unpage(original_global)
        changed_global,registration_changes=register(unpack_global(global_logical)[0],registration_evidence,ident)
        stored['Global/Latest']=original_global
        payloads['Global/Latest']=repack_global(global_logical,changed_global)
    ancillary_report=None
    if synchronize_ancillary:
        from project_information_codec import patch_timestamp
        stored['ProjectInformation']=original_project
        payloads['ProjectInformation'],ancillary_report=patch_timestamp(original_project,hashlib.sha256(original_project).hexdigest(),
            fields['m_increments'][-1]['m_atimeStamp']['m_lsb'],1792627200)
    dest.mkdir(parents=True,exist_ok=False);patches=[]
    for stream,payload in payloads.items():
        name=stream.replace('/','-')+'.bin';(dest/name).write_bytes(payload)
        patches.append({'stream':stream,'expected_stored_sha256':hashlib.sha256(stored[stream]).hexdigest(),'new_payload_file':name})
    (dest/'partition.bin').write_bytes(partition_encode(partition))
    manifest={'input_sha256':SOURCE_SHA,'patches':patches,'creates':[{'stream':'Partitions/66','expected_absent':True,'new_payload_file':'partition.bin'}]}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'source_sha256':SOURCE_SHA,'new_element_id':ident,'new_episode':39,'new_partition':'Partitions/66',
            'new_episode_guid':str(EPISODE),'new_storage_guid':str(STORAGE),'new_name':NAME,
            'source_rows':len(table.rows),'new_rows':len(newtable.rows),'prior_table_rows_byte_identical':newtable.rows[:-1]==table.rows,
            'channel_body_bytes':{str(s):len(b)for s,b in bodies.items()},
            'signature':'empty unsigned fields','root_registration':'three measured lists updated' if registration_evidence is not None else 'known missing three lists; Global/Latest unchanged',
            'registration_changes':registration_changes,
            'regular_ancillary_revision_policy_applied':synchronize_ancillary,'project_information_timestamp':ancillary_report,
            'hypotheses':['Existing ES schemas suffice for these bounded object fields.',
                          'IdentifierSource.m_last+1 and new creation episode allocate the identity.',
                          'One new ordinal partition stores one object; old partitions are retained.',
                          'Stream revisions follow the explicitly selected variant; preview/formats/partAtom remain unchanged.',
                          'Only the three measured registration lists are updated when requested; complete incoming registration requirements remain unproven.'],
            'autodesk_acceptance':'not_tested','complete_save_transaction':False,'production_native_export':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('dest',type=Path)
    p.add_argument('--profile',type=Path,default=Path(__file__).parent/'results/new-element-profile.json')
    p.add_argument('--identity-evidence',type=Path,default=Path(__file__).parent/'results/save-identity.json')
    p.add_argument('--registration-evidence',type=Path)
    p.add_argument('--synchronize-ancillary',action='store_true')
    p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args()
    print(json.dumps(make(a.source,a.dest,json.loads(a.profile.read_bytes()),json.loads(a.identity_evidence.read_bytes()),acknowledge_hypotheses=a.acknowledge_hypotheses,registration_evidence=json.loads(a.registration_evidence.read_bytes()) if a.registration_evidence else None,synchronize_ancillary=a.synchronize_ancillary),indent=2))
