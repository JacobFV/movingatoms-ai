"""Strict full-object graph validation with the pinned public reader."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from partition_segments import decode
from partition_objects import validate
from parameter_experiment import STREAM,ELEMENT
from schema_probe import REV


def run(source,files,target):
    source=source.resolve()
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    local=Path(__file__).resolve().parent/'local'
    with tempfile.TemporaryDirectory(dir=local) as directory:
        project=Path(directory);(project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-object-graph-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target.resolve())],check=True)
        reports=[]
        for path in files:
            with olefile.OleFileIO(path) as f:
                d=zlib.decompressobj(31);schema=d.decompress(unpage(f.openstream('Formats/Latest').read()))
                if not d.eof or d.unused_data:raise ValueError('invalid schema gzip')
                partition=decode(unpage(f.openstream(STREAM).read()))
                items=validate(partition.segments[0],8)[102]
                found=[r for r in items if r.element_id==ELEMENT]
                if len(found)!=1:raise ValueError('target object absent or ambiguous')
                (project/'schema.bin').write_bytes(schema);(project/'body.bin').write_bytes(found[0].body)
                result=json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-object-graph-probe'),str(project/'schema.bin'),str(project/'body.bin')]))
                reports.append({'file':path.name,'reader_commit':REV,'graph':result})
        return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.files,a.target),indent=2))
