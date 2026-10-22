"""Audit the first partition segment using explicit gzip lengths, not magic scans.

This is a bounded research parser, NOT a complete partition encoder. It stops
at the first segment terminator and records all remaining bytes as unresolved.
The 64-byte footer is recorded without claiming it is a checksum or signature.
"""
import argparse
from collections import Counter
import hashlib
import json
import struct
from pathlib import Path
import zlib
import olefile
from codec import decode

# Schema tags observed in the pinned 2023/2024/2025 fixtures.
TAGS = {0xE4E, 0xE7C, 0xED9}


def audit(raw):
    if len(raw)<44 or raw[:8]!=struct.pack('<II',9,0):
        raise ValueError('unsupported partition prefix')
    tag=struct.unpack_from('<H',raw,18)[0]
    if tag not in TAGS: raise ValueError('unsupported partition schema tag')
    pos=18
    members=[]
    digests={name:hashlib.sha512() for name in ('gzip_members','inflated_members')}
    while True:
        if pos+18>len(raw) or struct.unpack_from('<H',raw,pos)[0]!=tag:
            raise ValueError('missing next member/terminator tag')
        kind,count,stored,body=struct.unpack_from('<IIII',raw,pos+2)
        if kind==0:
            if count or stored or body: raise ValueError('invalid segment terminator')
            break
        if kind not in (4,5,6,7) or stored<8: raise ValueError('unsupported member kind/length')
        start=pos+26
        end=start+stored-8
        if end+6>len(raw): raise ValueError('truncated compressed member')
        compressed=raw[start:end]
        d=zlib.decompressobj(31)
        inflated=d.decompress(compressed)
        if not d.eof or d.unused_data: raise ValueError('member length does not match gzip EOF')
        if raw[end:end+6]!=struct.pack('<HI',tag-7,stored):
            raise ValueError('member trailer length/tag mismatch')
        digests['gzip_members'].update(compressed)
        digests['inflated_members'].update(inflated)
        overhead=len(inflated)-body
        members.append({'offset':pos,'kind':kind,'count':count,'stored_length_field':stored,
                        'gzip_bytes':len(compressed),'inflated_bytes':len(inflated),
                        'body_length_field':body,'overhead_bytes':overhead})
        pos=end+6
    footer=pos+18
    if footer+6>len(raw): raise ValueError('missing footer')
    footer_tag,length=struct.unpack_from('<HI',raw,footer)
    if length not in (0,64) or footer+6+length>len(raw): raise ValueError('unsupported footer length')
    field=raw[footer+6:footer+6+length]
    candidates={name:h.digest() for name,h in digests.items()}
    candidates.update({
        'segment_before_terminator':hashlib.sha512(raw[:pos]).digest(),
        'blocks_before_terminator':hashlib.sha512(raw[18:pos]).digest(),
        'segment_through_terminator':hashlib.sha512(raw[:footer]).digest(),
        'segment_through_footer_header':hashlib.sha512(raw[:footer+6]).digest(),
        'blake2b_segment':hashlib.blake2b(raw[:pos]).digest(),
    })
    matches=[name for name,value in candidates.items() if value==field or value[::-1]==field]
    return {'schema_tag':hex(tag),'members':members,'first_segment_end':pos,
            'remaining_bytes':len(raw)-pos,'footer_tag':hex(footer_tag),'footer_bytes':length,
            'footer_hex':field.hex(),'digest_candidates':list(candidates),'digest_matches':matches,
            'complete_partition_validation':False}


def verify(path):
    out=[]
    with olefile.OleFileIO(path) as f:
        for parts in f.listdir():
            if parts[0]!='Partitions':continue
            result=audit(decode(f.openstream(parts).read()))
            members=result.pop('members')
            result.update({'members_verified':len(members),
                           'gzip_bytes_verified':sum(m['gzip_bytes'] for m in members),
                           'inflated_bytes_verified':sum(m['inflated_bytes'] for m in members),
                           'kinds':dict(Counter(m['kind'] for m in members))})
            result['stream']='/'.join(parts)
            out.append(result)
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'partitions':out}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('files',type=Path,nargs='+')
    args=p.parse_args()
    print(json.dumps([verify(path) for path in args.files],indent=2))
