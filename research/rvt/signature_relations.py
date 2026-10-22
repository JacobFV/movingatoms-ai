"""Compare source-group identities without assuming a signature algorithm.

Reads only licensed source files. Equal-channel tests are exact-byte comparisons
represented by SHA-256; they do not claim all signature inputs are known.
"""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode
from partition_objects import records


def h(data): return hashlib.sha256(data).hexdigest()


def summarize_equal(items, key):
    groups = defaultdict(list)
    for item in items:
        value = item[key]
        if value is not None: groups[value].append(item)
    duplicates = [values for values in groups.values() if len(values)>1]
    return {'duplicate_sets':len(duplicates),'groups_in_duplicate_sets':sum(map(len,duplicates)),
            'sets_with_different_private_fields':sum(len({v['private'] for v in values})>1 for values in duplicates),
            'examples':[{'matching_value': values[0][key],
                'locations':[v['location'] for v in values],
                'different_private_fields':len({v['private'] for v in values})>1,
                'different_complete_inflated_inputs':len({v['all_channels'] for v in values})>1}
                for values in duplicates[:8]]}


def analyze(paths):
    rows=[]; files=[]; public=Counter(); empty=[]; base_pairs=[]
    for path in paths:
        file_rows=[]
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                p=decode(unpage(f.openstream(parts).read()));width=4 if p.root_tag==0x365 else 8
                for i,s in enumerate(p.segments):
                    groups=records(s,width)
                    location={'file':path.name,'stream':'/'.join(parts),'group':i,'count':s.count}
                    row={'location':location,'private':s.footer.hex(),'content_key':s.guid.hex() if s.guid else None,
                         'all_channels':h(b''.join(m.inflate() for m in s.members))}
                    for seq,items in groups.items():
                        # Include object IDs and body lengths so concatenation is unambiguous.
                        row[f'channel_{seq}']=h(b''.join(r.element_id.to_bytes(width,'little')+len(r.body).to_bytes(8,'little')+r.body for r in items))
                        row[f'body_{seq}']=h(b''.join(len(r.body).to_bytes(8,'little')+r.body for r in items))
                    row['id_set']={r.element_id for r in groups[101][:-1]}
                    row['object_hashes']={seq:{r.element_id:h(r.body) for r in items[:-1]} for seq,items in groups.items()}
                    row['empty_bodies']={str(seq):sum(not r.body for r in items[:-1]) for seq,items in groups.items()}
                    public[(len(s.footer),s.label.decode('utf-16le'))]+=1
                    if not s.count:empty.append({**location,'private_bytes':len(s.footer),'public_chars':len(s.label)//2})
                    rows.append(row);file_rows.append(row)
        # Base groups from different partitions may be retained history fragments;
        # numeric object identity alone is not proof of history ordering.
        base=[r for r in file_rows if r['content_key'] is None]
        for ai,a in enumerate(base):
            for b in base[ai+1:]:
                common=a['id_set'] & b['id_set']
                if common:
                    base_pairs.append({'left':a['location'],'right':b['location'],'shared_ids':len(common),
                        'same_private_field':a['private']==b['private'],
                        'same_object_bodies':{str(seq):sum(a['object_hashes'][seq][ident]==b['object_hashes'][seq][ident] for ident in common) for seq in (101,102,103)}})
        files.append({'file':path.name,'sha256':h(path.read_bytes()),'groups':len(file_rows)})
    # Exclude zero-count groups from simple-channel exclusion results.
    nonempty=[r for r in rows if r['location']['count']>0]
    content = defaultdict(list)
    for r in nonempty:
        if r['content_key'] is not None: content[r['content_key']].append(r)
    content_pairs=[]
    for key, values in content.items():
        for ai,a in enumerate(values):
            for b in values[ai+1:]:
                left_ids=list(a['object_hashes'][101]); right_ids=list(b['object_hashes'][101])
                deltas=Counter(right-left for left,right in zip(left_ids,right_ids))
                content_pairs.append({'content_key':key,'left':a['location'],'right':b['location'],
                    'equal_record_counts':len(left_ids)==len(right_ids),
                    'paired_records':min(len(left_ids),len(right_ids)),
                    'ordered_id_delta_counts':dict(sorted(deltas.items())),
                    'same_private_field':a['private']==b['private'],
                    'same_body_at_record_position':{str(seq):sum(x==y for x,y in zip(a['object_hashes'][seq].values(),b['object_hashes'][seq].values())) for seq in (101,102,103)}})
    keys=['content_key','all_channels']+[f'{kind}_{seq}' for kind in ('channel','body') for seq in (101,102,103)]
    return {'files':files,'groups':len(rows),'nonempty_groups':len(nonempty),
        'public_private_relations':[{'private_bytes':k[0],'public_text':k[1],'groups':n} for k,n in public.items()],
        'zero_element_groups':empty,
        'equal_input_relations_nonempty':{key:summarize_equal(nonempty,key) for key in keys},
        'base_group_shared_object_pairs':base_pairs,'same_content_key_pairs':content_pairs,
        'limits':['Same object IDs are compared only between base groups of one source file.',
                  'No episode order is inferred from partition names.',
                  'Different private fields for identical channel data reject only a deterministic function of that channel alone.',
                  'Randomized signatures, hidden context, and untested inputs remain possible.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('files',nargs='+',type=Path)
    print(json.dumps(analyze(parser.parse_args().files),indent=2))
