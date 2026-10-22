"""Reconcile independently schema-decoded increment metadata with object counts."""
import argparse
import json
from pathlib import Path


def reconcile(bookkeeping,objects):
    by_hash={x['sha256']:x for x in objects}
    if len(by_hash)!=len(objects):raise ValueError('duplicate object evidence')
    reports=[]
    for b in bookkeeping:
        if b['sha256'] not in by_hash:raise ValueError('missing matching object evidence')
        original=by_hash[b['sha256']]
        if b['history_root']['fields']['m_nextLocalSequenceNumber']!=b['episode_count']:
            raise ValueError('local sequence number differs from tested episode-count invariant')
        if any(int(n)>=b['episode_count'] for n in b['modification_episode_histogram']):
            raise ValueError('modification episode absent from History')
        streams={}
        for stream in original['streams']:
            ordinal=int(stream['stream'].split('/')[1])
            if ordinal in streams or ordinal>=len(b['increments']):raise ValueError('invalid increment ordinal')
            count=sum(g['declared_count'] for g in stream['segments'])
            increment=b['increments'][ordinal]
            if count!=increment['stored_elements']:raise ValueError('increment/object count mismatch')
            streams[ordinal]={'stream':stream['stream'],'base_objects':stream['segments'][0]['declared_count'],
                              'all_group_objects':count,'content_groups':len(stream['segments'])-1,
                              'greatest_episode':increment['greatest_episode'],
                              'total_episodes':increment['total_episodes']}
        active={i for i,v in enumerate(b['increments']) if v['stored_elements']}
        if not active.issubset(streams):raise ValueError('active increment has no physical stream')
        reports.append({'file':b['file'],'sha256':b['sha256'],'reader_commit':b['reader_commit'],
                        'history_episodes':b['episode_count'],'increment_entries':len(b['increments']),
                        'project_table_records':b['table_record_count'],
                        'table_partition_id_histogram':b['partition_id_histogram'],
                        'graveyard_records':b['graveyard_records'],
                        'next_local_sequence_equals_episode_count':True,
                        'modification_episodes_in_history':True,
                        'all_active_increments_present':True,'all_partition_counts_match':True,
                        'streams':list(streams.values()),
                        'history_root_field_spans':b['history_root']['field_spans'],
                        'increment_root_fields':list(b['increment_root']['fields']),
                        'room_identity':b['room_identity'],
                        'complete_save_semantics':'not_established'})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bookkeeping',type=Path);p.add_argument('objects',type=Path)
    a=p.parse_args();print(json.dumps(reconcile(json.loads(a.bookkeeping.read_bytes()),json.loads(a.objects.read_bytes())),indent=2))
