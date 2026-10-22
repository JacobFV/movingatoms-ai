"""Corpus verification of all partition envelopes and footer determinism probes."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import struct
import olefile
from codec import decode as unpage
from partition_segments import decode,encode,PROFILES


def verify(paths):
    files=[];groups=defaultdict(list)
    for path in paths:
        streams=[]
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                raw=unpage(f.openstream(parts).read());p=decode(raw)
                if encode(p)!=raw:raise ValueError(f'nonidentical envelope: {path} {parts}')
                segments=[]
                for index,s in enumerate(p.segments):
                    inflated=hashlib.sha256();compressed=hashlib.sha256()
                    hashes={k:hashlib.sha512() for k in ('inflated','gzip','blocks')}
                    kinds=Counter();total=0
                    for m in s.members:
                        data=m.inflate();total+=len(data);kinds[m.kind]+=1
                        inflated.update(data);compressed.update(m.compressed)
                        hashes['inflated'].update(data);hashes['gzip'].update(m.compressed)
                        stored=len(m.compressed)+8;tag=PROFILES[p.root_tag][0]
                        hashes['blocks'].update(struct.pack('<HIIIIQ',tag,m.kind,m.count,stored,m.body_length,m.sequence)+m.compressed+struct.pack('<HI',tag-7,stored))
                    match=[k for k,h in hashes.items() if s.footer in (h.digest(),h.digest()[::-1])]
                    record={'index':index,'count_field':s.count,'guid':s.guid.hex() if s.guid else None,
                            'members':len(s.members),'kinds':dict(kinds),'inflated_bytes':total,
                            'inflated_sha256':inflated.hexdigest(),'gzip_sha256':compressed.hexdigest(),
                            'footer_hex':s.footer.hex(),'sha512_matches':match}
                    segments.append(record)
                    groups[inflated.hexdigest()].append({'file':path.name,'stream':'/'.join(parts),
                                                        'index':index,'footer_hex':s.footer.hex()})
                guids=[s.guid for s in p.segments[1:]]
                streams.append({'stream':'/'.join(parts),'payload_bytes':len(raw),'byte_identical':True,
                                'trailing_zero':p.trailing_zero,'continuation_guids_byte_sorted':guids==sorted(guids),
                                'segments':segments})
        files.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'streams':streams})
    duplicates=[{'inflated_sha256':h,'occurrences':v,'same_footer':len({x['footer_hex'] for x in v})==1}
                for h,v in groups.items() if len(v)>1]
    return {'files':files,'duplicate_inflated_segments':duplicates,'semantic_validity':'not_established'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',type=Path,nargs='+')
    print(json.dumps(verify(p.parse_args().files),indent=2))
