"""Bind observed wire tags to names in file-embedded schemas using pinned rvt-rs.

Accepts a local checkout of the public clean-room reader; never reads Revit code.
The Rust helper's build artifacts are confined to ignored local research data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode
from partition_audit import audit

REV='b6086d41b9758fd9b92f42f0a47b8345b9c58056'


def run(source,files,target):
    source=source.resolve()
    rev=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if rev!=REV:raise ValueError('reader checkout is not the pinned revision')
    subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True,stdout=subprocess.DEVNULL)
    local=Path(__file__).resolve().parent/'local';local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=local) as directory:
        project=Path(directory);(project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-schema-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--manifest-path',str(project/'Cargo.toml'),'--release','--offline','--target-dir',str(target.resolve())],check=True)
        binary=target.resolve()/'release/rvt-schema-probe';reports=[]
        for path in files:
            with olefile.OleFileIO(path)as f:
                compressed=decode(f.openstream('Formats/Latest').read());d=zlib.decompressobj(31);schema=d.decompress(compressed)
                if not d.eof or d.unused_data:raise ValueError('unexpected schema compression framing')
                (project/'schema.bin').write_bytes(schema)
                result=json.loads(subprocess.check_output([str(binary),str(project/'schema.bin')]))
                first=next(p for p in f.listdir()if p[0]=='Partitions')
                payload=decode(f.openstream(first).read());a=audit(payload)
                tags={'ContentMarker':int.from_bytes(payload[8:10],'little'),
                      'ContentKey':int.from_bytes(payload[8:10],'little')-1,
                      'SegmentMarker':int(a['schema_tag'],16),
                      'SegmentCheckback':int(a['schema_tag'],16)-7,
                      'SignatureMarker':int(a['footer_tag'],16)}
                actual={c['name']:c['tag']for c in result['classes']}
                if actual!=tags:raise ValueError('schema class names do not match observed wire tags')
                result.update({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                               'partition_sample':'/'.join(first),'observed_tags_match':True,
                               'reader_revision':REV,'signature_algorithm':'unknown',
                               'autodesk_enforcement':'not_tested'})
                reports.append(result)
        return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',required=True,type=Path)
    p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/schema-target')
    p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.files,a.target),indent=2))
