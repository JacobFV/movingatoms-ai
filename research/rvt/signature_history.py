"""Strict source-only comparison of SignatureMarker across pinned Core history."""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import struct
import olefile
from codec import decode as unpage
from partition_segments import decode, encode, PROFILES


def h(data): return hashlib.sha256(data).hexdigest()


def differences(a,b):
    keys=('root_tag','count','content_key','public_field','member_layout','gzip_headers',
          'inflated_sha256','gzip_sha256','deflate_sha256','member_blocks_sha256',
          'group_index','is_last_group','partition_payload_sha256','stream')
    return [k for k in keys if a[k]!=b[k]]


def analyze(source_report,directory):
    provenance=json.loads(source_report.read_text());rows=[];files=[];partitions=[]
    for snapshot in provenance['snapshots']:
        path=directory/snapshot['file'];sha=h(path.read_bytes())
        if sha!=snapshot['sha256']:raise ValueError(f'fixture hash mismatch: {path}')
        groups=0
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                stored=f.openstream(parts).read();raw=unpage(stored);p=decode(raw)
                if encode(p)!=raw:raise ValueError('partition envelope roundtrip mismatch')
                stream='/'.join(parts)
                partitions.append({'file':path.name,'stream':stream,'stored_sha256':h(stored),'payload_sha256':h(raw)})
                for i,s in enumerate(p.segments):
                    tag=PROFILES[p.root_tag][0]
                    blocks=b''.join(struct.pack('<HIIIIQ',tag,m.kind,m.count,len(m.compressed)+8,m.body_length,m.sequence)+m.compressed+struct.pack('<HI',tag-7,len(m.compressed)+8) for m in s.members)
                    # gzip header/trailer independence is explicitly limited to FLG=0.
                    if any(m.compressed[:3]!=b'\x1f\x8b\x08' or m.compressed[3]!=0 for m in s.members):
                        raise ValueError('cannot compare deflate bytes for nonstandard gzip header')
                    rows.append({'file':path.name,'stream':stream,'group_index':i,'count':s.count,
                        'root_tag':p.root_tag,'content_key':s.guid.hex() if s.guid else None,
                        'private_field':s.footer.hex(),'public_field':s.label.hex(),
                        'is_last_group':i==len(p.segments)-1,
                        'member_layout':[[m.kind,m.count,m.body_length,m.sequence,len(m.compressed)] for m in s.members],
                        'gzip_headers':[m.compressed[:10].hex() for m in s.members],
                        'inflated_sha256':h(b''.join(m.inflate() for m in s.members)),
                        'gzip_sha256':h(b''.join(m.compressed for m in s.members)),
                        'deflate_sha256':h(b''.join(m.compressed[10:-8] for m in s.members)),
                        'member_blocks_sha256':h(blocks),'partition_payload_sha256':h(raw)})
                    groups+=1
        files.append({'file':path.name,'sha256':sha,'groups':groups,'commit':snapshot['commit']})
    byinput=defaultdict(list)
    for row in rows:byinput[row['inflated_sha256']].append(row)
    sets=[];equalpairs=0;unequalpairs=0;patterns=Counter();examples=[]
    for digest,items in byinput.items():
        if len(items)<2:continue
        sets.append({'inflated_sha256':digest,'occurrences':len(items),'private_variants':len({x['private_field'] for x in items}),
                     'locations':[{'file':x['file'],'stream':x['stream'],'group':x['group_index']} for x in items]})
        for ai,a in enumerate(items):
            for b in items[ai+1:]:
                if a['private_field']==b['private_field']:equalpairs+=1
                else:
                    unequalpairs+=1;diff=differences(a,b);patterns[tuple(diff)]+=1
                    if len(examples)<20:examples.append({'left':a,'right':b,'different_fields':diff})
    byfooter=defaultdict(list)
    for row in rows:
        if row['private_field']:byfooter[row['private_field']].append(row)
    footer_variants=[]
    for footer, items in byfooter.items():
        if len(items)<2:continue
        footer_variants.append({'private_field_sha256':h(bytes.fromhex(footer)),
            'occurrences':len(items),'inflated_variants':len({x['inflated_sha256'] for x in items}),
            'gzip_variants':len({x['gzip_sha256'] for x in items}),
            'member_blocks_variants':len({x['member_blocks_sha256'] for x in items}),
            'locations':[{'file':x['file'],'stream':x['stream'],'group':x['group_index']} for x in items]})
    bypartition=defaultdict(list)
    for p in partitions:bypartition[p['payload_sha256']].append(p)
    return {'source_provenance_report':str(source_report),'files':files,'total_groups':len(rows),
        'equal_inflated_sets':sets,'equal_inflated_pair_counts':{'same_private_field':equalpairs,'different_private_field':unequalpairs},
        'different_private_field_difference_patterns':[{'different_fields':list(k),'pairs':v} for k,v in patterns.items()],
        'different_private_field_examples':examples,'repeated_private_fields':footer_variants,
        'repeated_complete_partition_payloads':[v for v in bypartition.values() if len(v)>1],
        'limitations':['Git snapshot sequence is not necessarily adjacent Revit saves.',
                      'Group-local equal bytes do not establish equal file-wide signing context.',
                      'Retained old groups can carry old signatures; matching fields across snapshots do not prove regeneration.',
                      'No proprietary implementation, key, or enforcement behavior is observed.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,default=Path(__file__).parent/'results/paired-save-sources.json')
    p.add_argument('--directory',type=Path,default=Path(__file__).parent/'local')
    a=p.parse_args();print(json.dumps(analyze(a.sources,a.directory),indent=2))
