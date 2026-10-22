"""Repack every licensed corpus object and compare complete record bodies."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode,encode
from partition_objects import validate
from object_writer import pack_records


def verify(paths):
    reports=[]
    for path in paths:
        groups=records=members=0
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                original=decode(unpage(f.openstream(parts).read()))
                width=4 if original.root_tag==0x365 else 8
                segments=[]
                for segment in original.segments:
                    expected=validate(segment,width)
                    packed=tuple(m for seq,items in expected.items() for m in pack_records(items,seq,width))
                    updated=replace(segment,members=packed)
                    if validate(updated,width)!=expected:raise ValueError('repacked record bodies differ')
                    segments.append(updated);groups+=1;members+=len(packed)
                    records+=sum(len(items) for items in expected.values())
                new=replace(original,segments=tuple(segments))
                if decode(encode(new))!=new:raise ValueError('partition envelope failed round trip')
        reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'content_groups':groups,'object_records':records,'repacked_members':members,
                        'all_ids_bodies_counts_and_checksums_preserved':True,
                        'partition_envelope_round_trip':True,'autodesk_acceptance':'not_tested'})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',type=Path,nargs='+')
    print(json.dumps(verify(p.parse_args().files),indent=2))
