"""Read one current indexed record using pinned independent routing and graph decode."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from schema_probe import REV


def run(source,files,target,element):
    if not 0<=element<2**64-1:raise ValueError('invalid element ID')
    source=source.resolve()
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    local=Path(__file__).resolve().parent/'local';local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=local) as directory:
        project=Path(directory);(project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-current-record-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target.resolve())],check=True)
        reports=[]
        for path in files:
            result=json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-current-record-probe'),str(path.resolve()),str(element)]))
            reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'reader_commit':REV,**result})
        return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--element',type=int,required=True);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.files,a.target,a.element),indent=2))
