"""Compare same-lineage licensed snapshots; chronology is not a controlled edit."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import uuid
import zlib
import olefile
from codec import decode as unpage
from element_table import decode as table_decode
from save_history import decode as history_decode
from save_increments import decode as increments_decode
from partition_segments import decode as partition_decode
from partition_objects import validate
from increment_routing import select_record


def read_snapshot(path, expected_sha):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_sha:raise ValueError('snapshot hash mismatch')
    with olefile.OleFileIO(path) as f:
        def global_body(name):
            logical=unpage(f.openstream('Global/'+name).read());d=zlib.decompressobj(31)
            raw=d.decompress(logical[8:])
            if not d.eof or d.unconsumed_tail:raise ValueError('invalid global gzip')
            return raw
        history=history_decode(global_body('History'))
        table=table_decode(global_body('ElemTable'),8)
        _,increment_fields=increments_decode(global_body('DocumentIncrementTable'))
        increments=[]
        if increment_fields['m_permutation']:raise ValueError('permuted snapshots unsupported')
        for r in increment_fields['m_increments']:
            increments.append({'greatest_episode':r['m_greatest']['m_id'],
                'stored_elements':r['m_totalElements'],
                'redirects':[(v['m_causedByIncrementNumber'],v['m_totalElements']) for v in r['m_incrementVersions']]})
        holders=defaultdict(dict);present=set()
        for parts in f.listdir():
            if parts[0]!='Partitions':continue
            ordinal=int(parts[1]);present.add(ordinal)
            partition=partition_decode(unpage(f.openstream(parts).read()))
            if partition.root_tag!=0x37b:raise ValueError('requires tested 2024 partition profile')
            records=validate(partition.segments[0],8)
            for seq,channel in records.items():
                for record in channel[:-1]:
                    holders[record.element_id].setdefault(ordinal,{})[seq]=hashlib.sha256(record.body).hexdigest()
    identities={};reasons=Counter();unresolved=[]
    for row in table.rows:
        element=table.current(row)
        c,m,u=[int.from_bytes(row[a:a+4],'little') for a in (8,12,16)]
        if c>=len(history.episodes):raise ValueError('creation outside History')
        original=table.primary(row)
        unique=str(uuid.UUID(bytes_le=history.episodes[-1-c][:16]))+f'-{original:08x}'
        try:
            selected,reason=select_record(m,increments,present,holders[element])
            body=holders[element][selected];reasons[reason]+=1
        except ValueError as error:
            selected=None;body=None;reason=str(error)
            unresolved.append({'element':element,'error':reason})
        identities[element]={'unique_id':unique,'creation':c,'modification':m,'user_modification':u,
                             'selected_increment':selected,'selection_reason':reason,'bodies':body}
    return {'path':path.name,'sha256':expected_sha,'episodes':history.episodes,'rows':identities,
            'increment_fields':increment_fields,'selection_counts':dict(reasons),'unresolved':unresolved}


def compare(before,after):
    old_episodes,new_episodes=before['episodes'],after['episodes']
    if (not old_episodes or len(new_episodes)<len(old_episodes)
            or new_episodes[-len(old_episodes):]!=old_episodes):
        raise ValueError('episode lineage is not a preserved chronological suffix')
    old,new=before['rows'],after['rows'];shared=sorted(old.keys()&new.keys())
    matrix=Counter();examples=defaultdict(list);identity_changed=[];unresolved=[]
    for element in shared:
        a,b=old[element],new[element]
        if a['unique_id']!=b['unique_id']:
            identity_changed.append(element);continue
        if a['bodies'] is None or b['bodies'] is None:unresolved.append(element);continue
        channels=tuple(seq for seq in (101,102,103) if a['bodies'][seq]!=b['bodies'][seq])
        m='same' if a['modification']==b['modification'] else 'increased' if b['modification']>a['modification'] else 'decreased'
        u='same' if a['user_modification']==b['user_modification'] else 'sentinel_to_episode' if a['user_modification']==0xffffffff else 'episode_to_sentinel' if b['user_modification']==0xffffffff else 'increased' if b['user_modification']>a['user_modification'] else 'decreased'
        label=f'body_channels={",".join(map(str,channels)) or "unchanged"};modification={m};user={u}'
        matrix[label]+=1
        if len(examples[label])<10:
            examples[label].append({'element':element,'before_episodes':[a[k] for k in ('creation','modification','user_modification')],
                                  'after_episodes':[b[k] for k in ('creation','modification','user_modification')],
                                  'before_increment':a['selected_increment'],'after_increment':b['selected_increment'],
                                  'selection_reasons':[a['selection_reason'],b['selection_reason']]})
    def summary(s):
        last=s['increment_fields']['m_increments'][-1]
        return {'file':s['path'],'sha256':s['sha256'],'project_rows':len(s['rows']),
                'history_episodes':len(s['episodes']),'increments':len(s['increment_fields']['m_increments']),
                'last_increment':{k:v for k,v in last.items() if k.endswith('StreamRevision') or k in
                                 ('m_majorVersion','m_greatest','m_totalEpisodes','m_totalElements','m_atimeStamp')},
                'selection_counts':s['selection_counts'],'unresolved_selections':s['unresolved']}
    old_episodes=before['episodes'];new_episodes=after['episodes']
    return {'before':summary(before),'after':summary(after),
            'old_episode_mapping_is_suffix':len(new_episodes)>=len(old_episodes) and new_episodes[-len(old_episodes):]==old_episodes,
            'added_project_ids':sorted(new.keys()-old.keys()),'removed_project_ids':sorted(old.keys()-new.keys()),
            'shared_project_ids':len(shared),'shared_ids_with_changed_native_unique_id':identity_changed,
            'shared_ids_with_unresolved_body_selection':unresolved,
            'transition_counts':dict(sorted(matrix.items())),
            'transition_examples':dict(sorted(examples.items())),
            'controlled_edit_sequence':False,'autodesk_save_rule_inferred':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path)
    p.add_argument('--before-sha256',required=True);p.add_argument('--after-sha256',required=True);a=p.parse_args()
    print(json.dumps(compare(read_snapshot(a.before,a.before_sha256),read_snapshot(a.after,a.after_sha256)),indent=2))
