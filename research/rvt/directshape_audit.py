"""Read-only current DirectShape corpus inventory through pinned public reader."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from fetch_fixture import FILES,HOLDOUTS
from schema_probe import REV


def inventory(reader,binary,destination):
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    base=Path(__file__).parent/'local';fixtures=[(name,sha)for _,name,sha in FILES]+HOLDOUTS
    for name,sha in fixtures:
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=sha:raise ValueError('fixture hash differs')
    def run(item):
        name,sha=item;data=json.loads(subprocess.check_output([str(binary),str(base/name)]))
        out=base/(Path(name).stem+'-directshape-inventory.json');out.write_text(json.dumps(data,indent=2)+'\n')
        return {'file':name,'sha256':sha,'records':data['records'],'summary':data['summary'],'inventory_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,fixtures))
    result={'reader_revision':REV,'probe_source_sha256':hashlib.sha256(Path(__file__).with_name('directshape_probe.rs').read_bytes()).hexdigest(),
            'probe_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'fixtures':rows,'scope':'Current routed DirectShape/DirectShapeType, all three channels; file bytes and public reader only.'}
    destination.write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=inventory(a.reader_source,a.binary,a.result)
    print(json.dumps([{'file':f['file'],'records':len(f['records'])}for f in result['fixtures']],indent=2))
