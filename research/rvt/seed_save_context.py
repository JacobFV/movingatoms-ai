"""Measured minimal-seed save context and explicitly hypothetical append plan."""
import argparse,hashlib,json,struct,subprocess,tempfile,uuid,zlib
from pathlib import Path
import olefile
import element_table,save_history,save_increments,basic_file_info_codec
from codec import decode as unpage
from save_candidate import unpack_global,append_increment
from new_element import allocate_identity
from project_information_codec import parse as parse_project
from datetime import datetime
SOURCE_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'

def allocation_plan(table,history,fields,count,timestamp,guid):
    if type(count)is not int or not 1<=count<=100:raise ValueError('requires 1..100 elements')
    if table.width!=8:raise ValueError('requires measured 64-bit table')
    allocated=[];newtable=table
    for _ in range(count):
        identity,newtable=allocate_identity(newtable,history)
        allocated.append(identity)
    newhistory=save_history.prepend_episode(history,uuid.UUID(guid).bytes_le)
    changed=append_increment(fields,history.next_sequence,timestamp)
    for key in ('m_increments','m_localIncrements'):
        changed[key][-1]['m_totalElements']=count
        changed[key][-1]['m_incrementVersions'][0]['m_totalElements']=count
    return {'first_id':table.last_id+1,'last_id':newtable.last_id,'new_episode_id':history.next_sequence,
            'partition_ordinal_hypothesis':len(fields['m_increments']),'new_major_version':changed['m_increments'][-1]['m_majorVersion'],
            'allocated':allocated,'history_episodes_after':len(newhistory.episodes),'increment_fields':changed}

def audit(source,probe,identity_probe,count=1):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('seed hash differs')
    with olefile.OleFileIO(source)as f:
        stored={'/'.join(n):f.openstream(n).read()for n in f.listdir()}
    raw={name:unpack_global(unpage(stored['Global/'+name]))[0]for name in ('History','ElemTable','DocumentIncrementTable','Latest')}
    history=save_history.decode(raw['History']);table=element_table.decode(raw['ElemTable'],8);tag,fields=save_increments.decode(raw['DocumentIncrementTable'])
    assert save_history.encode(history)==raw['History'] and element_table.encode(table)==raw['ElemTable'] and save_increments.encode(tag,fields)==raw['DocumentIncrementTable']
    latest=fields['m_increments'][-1];basic=basic_file_info_codec.decode(stored['BasicFileInfo']);assert basic_file_info_codec.encode(basic)==stored['BasicFileInfo']
    contents=unpage(stored['Contents']);at=contents.index(b'\x1f\x8b\x08');d=zlib.decompressobj(31);body=d.decompress(contents[at:]);assert d.eof and not d.unconsumed_tail;contents_suffix=d.unused_data
    schema=zlib.decompress(unpage(stored['Formats/Latest']),31)
    with tempfile.TemporaryDirectory()as tmp:
        tmp=Path(tmp)
        for name,data in [('schema',schema),('contents',body),('basic',stored['BasicFileInfo']),('latest',raw['Latest']),('graph',raw['Latest'][:-4])]: (tmp/(name+'.bin')).write_bytes(data)
        identity=json.loads(subprocess.check_output([str(identity_probe),str(tmp)]))
        graph=json.loads(subprocess.check_output([str(probe),'decode',str(tmp/'schema.bin'),str(tmp/'graph.bin')]))['graph']
        tracker_probe=Path(__file__).parent/'local/schema-target/release/rvt-seed-save-context'
        tracker_evidence=json.loads(subprocess.check_output([str(tracker_probe),str(tmp/'schema.bin'),str(tmp/'graph.bin')]))
    assert graph['consumed_bytes']==len(raw['Latest'])-4
    trackers=[o for o in graph['objects']if o['class_name']=='StructuralElemSetTracking'];assert len(trackers)==1
    tracker=trackers[0];assert tracker['fields']['m_elemIdSet']==[]
    revisions=identity['contents_root']['fields']['m_streamRevisions'];assert all(latest[k]==v for k,v in revisions.items())
    assert basic.increments==len(fields['m_increments'])==latest['m_majorVersion']
    assert uuid.UUID(basic.guid).bytes_le==history.episodes[0][:16]
    _,stamp,*_=parse_project(stored['ProjectInformation']);offset=latest['m_atimeStamp']['m_lsb']-int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp())
    plan=allocation_plan(table,history,fields,count,latest['m_atimeStamp']['m_lsb']+60,'67876160-3898-55f4-a25a-4b9dfc3e4ab3')
    # Never publish actor metadata from decoded increment rows.
    plan.pop('increment_fields')
    return {'source_sha256':SOURCE_SHA,'schema_sha256':hashlib.sha256(schema).hexdigest(),'stream_names':list(stored),'codecs_exact_roundtrip':True,
      'table':element_table.validate(table),'history_episodes':len(history.episodes),'history_next_sequence':history.next_sequence,'increment_count':len(fields['m_increments']),
      'latest_revisions':{k:latest[k]for k in latest if k.endswith('StreamRevision')},'latest_overwrite':latest['m_overwrite'],
      'contents_logical_sha256':hashlib.sha256(contents).hexdigest(),'contents_inflated_sha256':hashlib.sha256(body).hexdigest(),'contents_inflated_hex':body.hex(),'contents_header_hex':contents[:at].hex(),'contents_gzip_suffix_hex':contents_suffix.hex(),'contents_gzip_offset':at,'contents_root':identity['contents_root'],'contents_revisions_match_increment':True,'formats_wrapper_revision':struct.unpack_from('<i',contents,at-4)[0],
      'bfi_counter_and_episode_match':True,'project_information_source_offset_seconds':offset,'existing_project_timestamp_patcher_accepts_offset':offset in (14400,36000),
      'global_complete_graph_objects':len(graph['objects']),'global_graph_bytes':graph['consumed_bytes'],'empty_structural_tracker':tracker,'registration_evidence':{'inflated_sha256':hashlib.sha256(raw['Latest']).hexdigest(),'objects':tracker_evidence['objects']},'project_information_sha256':hashlib.sha256(stored['ProjectInformation']).hexdigest(),
      'plan':plan,'unproven':['Partition ordinal 1 is proposed by prior corpus convention, not seed paired-save evidence.','Populating empty structural tracker for a first wall needs an explicit seed-specific policy.','Ancillary revision policy, timestamp offset preservation, and unsigned save acceptance remain hypotheses.','Wall type/material/level/style mapping and missing upper level are separate required work.']}
def register_seed(raw,evidence,wall_ids,level_ids):
    """Source-bound first-wall/upper-level tracking policy; no view creation."""
    from new_element_registration import id_set_bytes
    if hashlib.sha256(raw).hexdigest()!=evidence['inflated_sha256']:raise ValueError('seed Global hash differs')
    all_ids=wall_ids+level_ids
    if not all_ids or len(all_ids)!=len(set(all_ids)) or any(type(i)is not int or not 2746<=i<2**31 for i in all_ids):raise ValueError('invalid seed IDs')
    objects={o['class_name']:o for o in evidence['objects']}
    if len(objects)!=3 or set(objects)!={'StructuralElemSetTracking','DatumTracking','ElementTrackingData'}:raise ValueError('tracker inventory differs')
    patches=[];report=[]
    def add(obj,span,old,new,role):
        start,end=span['start'],span['end']
        if raw[start:end]!=id_set_bytes(old) or set(old)&set(new):raise ValueError('tracker span/source differs')
        after=sorted(old+new);patches.append((start,end,id_set_bytes(after)));report.append({'class':obj['class_name'],'role':role,'before':old,'after':after,'span':span})
    for name,expected,new in [('StructuralElemSetTracking',[],wall_ids),('DatumTracking',[1916],level_ids)]:
        obj=objects[name];old=[x['m_id']['m_id64']for x in obj['fields']['m_elemIdSet']]
        spans=[x for x in obj['field_spans']if x['name']=='m_elemIdSet']
        if old!=expected or len(spans)!=1:raise ValueError('unmeasured simple tracker')
        if new:add(obj,spans[0],old,new,'instance registration hypothesis')
    obj=objects['ElementTrackingData'];items=obj['fields']['m_elems']
    containers=[x for x in obj['field_spans']if x['name']=='m_elems']
    if len(containers)!=1:raise ValueError('ambiguous category container')
    container=containers[0]
    spans=[x for x in obj['field_spans']if x['name']=='m_elemIdSet' and container['start']<=x['start']<x['end']<=container['end']]
    if len(spans)!=len(items):raise ValueError('missing category spans')
    matches=[(i,x)for i,x in enumerate(items)if x['m_categoryId']['m_id']['m_id64']==-2000240]
    if len(matches)!=1:raise ValueError('ambiguous level category')
    i,item=matches[0];old=[x['m_id']['m_id64']for x in item['m_elemIdSet']]
    if old!=[1916]:raise ValueError('unmeasured level category')
    if level_ids:add(obj,spans[i],old,level_ids,'level category registration hypothesis')
    patches.sort()
    if any(a[1]>b[0]for a,b in zip(patches,patches[1:])):raise ValueError('overlapping tracker patches')
    result=raw
    for start,end,value in reversed(patches):result=result[:start]+value+result[end:]
    return result,report

def patch_seed_contents(logical,evidence,revisions):
    """Preserve the measured one-byte zero suffix without relaxing shared codec."""
    from save_identity import inflated,patch_contents_payload
    expected='0310c9b003961ae56591b02864d56b3ccbc147b52d6d47daee426c68bbf00b2c'
    if hashlib.sha256(logical).hexdigest()!=expected or evidence['contents_logical_sha256']!=expected:
        raise ValueError('seed Contents source differs')
    header=bytes.fromhex(evidence['contents_header_hex'])
    _,suffix=inflated(logical,len(header))
    if suffix!=b'\0' or evidence['contents_gzip_suffix_hex']!='00':raise ValueError('unmeasured seed Contents suffix')
    trimmed=logical[:-1];adapted=dict(evidence)
    adapted['contents_logical_sha256']=hashlib.sha256(trimmed).hexdigest()
    adapted['contents_gzip_suffix_hex']=''
    changed=patch_contents_payload(trimmed,adapted,revisions)+suffix
    _,new_suffix=inflated(changed,len(header))
    if new_suffix!=suffix:raise ValueError('seed Contents suffix changed')
    return changed

def patch_seed_timestamp(source,oldts,newts):
    """Pinned ProjectInformation layout with measured 10800-second offset."""
    from datetime import timezone
    if hashlib.sha256(source).hexdigest()!='b6a1864ff3c4a842e1daa1335323b1c2cc1ec3782a722b2f82d12365cc249d34':raise ValueError('seed ProjectInformation hash differs')
    if any(type(x)is not int or not 0<=x<=0xffffffff for x in (oldts,newts))or newts<oldts:raise ValueError('invalid timestamps')
    raw,stamp,start,central,end=parse_project(source)
    offset=oldts-int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp())
    if offset!=10800:raise ValueError('seed timestamp offset differs')
    newstamp=datetime.fromtimestamp(newts-offset,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ');updated=raw.replace(stamp.encode(),newstamp.encode())
    report={'source_sha256':hashlib.sha256(source).hexdigest(),'source_timestamp_offset_seconds':offset,'policy':'preserve measured seed offset hypothesis','all_other_xml_bytes_preserved':True}
    if updated==raw:return source,report
    c=zlib.compressobj(9,wbits=-15);compressed=c.compress(updated)+c.flush();crc=zlib.crc32(updated)
    local=bytearray(source[:start]);directory=bytearray(source[central:end]);closing=bytearray(source[end:])
    struct.pack_into('<III',local,14,crc,len(compressed),len(updated));struct.pack_into('<III',directory,16,crc,len(compressed),len(updated));struct.pack_into('<I',closing,16,len(local)+len(compressed))
    result=bytes(local)+compressed+bytes(directory)+bytes(closing)
    if parse_project(result)[0]!=updated:raise ValueError('XML verify failed')
    report['output_sha256']=hashlib.sha256(result).hexdigest();return result,report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--probe',type=Path,required=True);p.add_argument('--identity-probe',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args();a.result.write_text(json.dumps(audit(a.source,a.probe,a.identity_probe),indent=2)+'\n')
