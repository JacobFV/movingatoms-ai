"""Schema-directed History, increment and project-index bookkeeping evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
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
        (project/'Cargo.toml').write_text('[package]\nname="rvt-bookkeeping-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target.resolve())],check=True)
        reports=[]
        for path in files:
            suffixes={}
            with olefile.OleFileIO(path) as f:
                for filename,stream,offset in [('schema','Formats/Latest',0),('history','Global/History',8),
                        ('table','Global/ElemTable',8),('increments','Global/DocumentIncrementTable',8)]:
                    logical=unpage(f.openstream(stream).read());d=zlib.decompressobj(31)
                    data=d.decompress(logical[offset:])
                    if not d.eof or d.unconsumed_tail:raise ValueError('invalid global gzip')
                    suffixes[stream]={'bytes':len(d.unused_data),'sha256':hashlib.sha256(d.unused_data).hexdigest()}
                    (project/(filename+'.bin')).write_bytes(data)
                result=json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-bookkeeping-probe'),str(project)]))
                reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                'reader_commit':REV,'opaque_suffixes':suffixes,**result})
        return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.files,a.target),indent=2))
