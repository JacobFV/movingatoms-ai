"""Compare complete candidate records for unresolved project storage routes."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode
from partition_objects import validate


def verify(root,routing):
    reports=[]
    for report in routing:
        unresolved=report['unresolved_routes']
        if not unresolved:continue
        path=root/report['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=report['sha256']:
            raise ValueError('fixture hash mismatch')
        ids={r['element'] for r in unresolved};candidates={i:{} for i in ids}
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                p=decode(unpage(f.openstream(parts).read()));width=4 if p.root_tag==0x365 else 8
                for seq,items in validate(p.segments[0],width).items():
                    for r in items:
                        if r.element_id in ids:
                            candidates[r.element_id].setdefault(int(parts[1]),{})[seq]=hashlib.sha256(r.body).hexdigest()
        for r in unresolved:
            found=candidates[r['element']]
            if sorted(found)!=r['holder_increments']:raise ValueError('candidate set mismatch')
            if any(set(g)!={101,102,103} for g in found.values()):raise ValueError('candidate missing channel')
            hashes=list(found.values())
            reports.append({'file':report['file'],**r,'candidate_body_sha256':found,
                            'all_candidate_bodies_equal':bool(hashes) and all(h==hashes[0] for h in hashes),
                            'current_storage_route_resolved':False})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('routing',type=Path)
    a=p.parse_args();print(json.dumps(verify(a.root,json.loads(a.routing.read_bytes())),indent=2))
