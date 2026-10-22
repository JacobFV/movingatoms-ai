"""Audit exact increment routes without guessing current-record fallbacks."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from element_table import decode as table_decode
from partition_segments import decode
from partition_objects import validate
from verify_element_tables import inflate
from increment_routing import route


def verify(files,evidence):
    evidence={x['sha256']:x for x in evidence};reports=[]
    for path in files:
        digest=hashlib.sha256(path.read_bytes()).hexdigest();b=evidence[digest]
        with olefile.OleFileIO(path) as f:
            holders={};present=set();width=None
            for parts in f.listdir():
                if parts[0]!='Partitions':continue
                ordinal=int(parts[1]);present.add(ordinal)
                p=decode(unpage(f.openstream(parts).read()));width=4 if p.root_tag==0x365 else 8
                groups=validate(p.segments[0],width)
                for r in groups[101][:-1]:holders.setdefault(r.element_id,set()).add(ordinal)
            table=table_decode(inflate(unpage(f.openstream('Global/ElemTable').read())),width)
            misses=[];multiple=0
            for row in table.rows:
                ident=table.current(row);revision=int.from_bytes(row[12:16],'little')
                target=route(revision,b['increments'],present)
                found=holders.get(ident,set())
                multiple+=len(found)>1
                if target not in found:misses.append({'element':ident,'modification_episode':revision,
                                                      'routed_increment':target,'holder_increments':sorted(found)})
            reports.append({'file':path.name,'sha256':digest,'project_records':len(table.rows),
                            'multiple_base_group_candidates':multiple,'exact_route_matches':len(table.rows)-len(misses),
                            'unresolved_routes':misses,'highest_stream_fallback_used':False})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bookkeeping',type=Path,required=True)
    p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(verify(a.files,json.loads(a.bookkeeping.read_bytes())),indent=2))
