"""Report conservative physical selection separately from proven routing causes."""
import argparse
import json
from pathlib import Path
from increment_routing import select_record


def resolve(bookkeeping,routing,objects):
    books={b['sha256']:b for b in bookkeeping};physical={b['sha256']:b for b in objects}
    reports=[]
    for audit in routing:
        book=books[audit['sha256']]
        present={int(s['stream'].split('/')[1]) for s in physical[audit['sha256']]['streams']}
        cases=[]
        for case in audit['unresolved_routes']:
            selected,reason=select_record(case['modification_episode'],book['increments'],present,case['holder_increments'])
            cases.append({**case,'selected_increment':selected,'selection_evidence':reason})
        reports.append({'file':audit['file'],'sha256':audit['sha256'],
                        'exact_episode_routes':audit['exact_route_matches'],
                        'unique_compaction_history_holders':sum(c['selection_evidence']=='unique_compaction_history_holder' for c in cases),
                        'sole_holders_with_unresolved_history':sum(c['selection_evidence']=='sole_physical_holder_history_unresolved' for c in cases),
                        'highest_stream_fallback_used':False,'candidates':cases,
                        'autodesk_current_record_selection':'not_tested'})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bookkeeping','routing','objects'):p.add_argument(name,type=Path)
    a=p.parse_args();print(json.dumps(resolve(*[json.loads(getattr(a,n).read_bytes()) for n in ('bookkeeping','routing','objects')]),indent=2))
