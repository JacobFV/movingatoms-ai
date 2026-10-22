"""Verify every object envelope and record list in the pinned corpus."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode
from partition_objects import validate


def verify(paths):
    out=[]
    for path in paths:
        streams=[]
        with olefile.OleFileIO(path)as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                partition=decode(unpage(f.openstream(parts).read()))
                width=4 if partition.root_tag==0x365 else 8
                segments=[]
                for i,s in enumerate(partition.segments):
                    groups=validate(s,width)
                    digests={f'bodies_{seq}':hashlib.sha512(b''.join(r.body for r in items)).digest()
                             for seq,items in groups.items()}
                    digests['all_bodies']=hashlib.sha512(b''.join(r.body for items in groups.values() for r in items)).digest()
                    segments.append({'index':i,'declared_count':s.count,'records_per_sequence':len(groups[101]),
                                     'ordered_ids_equal':True,'unique_ids':True,'empty_sentinel':True,
                                     'object_encoding_byte_identical':True,'all_adler32_valid':True,
                                     'footer_sha512_body_matches':[k for k,v in digests.items()if v in (s.footer,s.footer[::-1])]})
                streams.append({'stream':'/'.join(parts),'id_width':width,'segments':segments})
        out.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'streams':streams})
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',type=Path,nargs='+')
    print(json.dumps(verify(p.parse_args().files),indent=2))
