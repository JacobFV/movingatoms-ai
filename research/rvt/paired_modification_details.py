"""Byte-level evidence for changed headers with unchanged modification episodes."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode
from partition_objects import validate


def inspect(pair_report,directory):
    results=[]
    for pair in pair_report['pairs']:
        cases=pair['transition_examples'].get('body_channels=101;modification=same;user=same',[])
        if not cases:continue
        if len(cases)!=pair['transition_counts']['body_channels=101;modification=same;user=same']:
            raise ValueError('example cap omits required cases')
        bodies=[]
        for side in ('before','after'):
            source=pair[side];path=directory/source['file']
            if path.parent.resolve()!=directory.resolve() or hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
                raise ValueError('snapshot mismatch')
            with olefile.OleFileIO(path) as f:
                found={}
                for increment in {c[f'{side}_increment'] for c in cases}:
                    p=decode(unpage(f.openstream(f'Partitions/{increment}').read()))
                    for record in validate(p.segments[0],8)[101]:
                        if record.element_id in {c['element'] for c in cases}: found[record.element_id]=record.body
                bodies.append(found)
        for case in cases:
            a,b=(side[case['element']] for side in bodies)
            delta=[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            results.append({'before':pair['before']['file'],'after':pair['after']['file'],**case,
                'before_bytes':len(a),'after_bytes':len(b),'before_sha256':hashlib.sha256(a).hexdigest(),
                'after_sha256':hashlib.sha256(b).hexdigest(),'changed_overlapping_bytes':delta,
                'trailing_bytes_before':a[min(len(a),len(b)):].hex(),
                'trailing_bytes_after':b[min(len(a),len(b)):].hex(),
                'byte_offsets_are_native_record_body_relative':True,'semantic_cause':'not_established'})
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('directory',type=Path)
    a=p.parse_args();print(json.dumps(inspect(json.loads(a.report.read_bytes()),a.directory),indent=2))
