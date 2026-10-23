"""Fetch license/hash-pinned candidate empty seeds and inventory without mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from schema_probe import REV

SOURCES=[
    {'repo':'ricaun-io/ricaun.Revit.FileInfo','commit':'9228ef12063fd294a565c47b989449ab93460a61',
     'license':'MIT','license_path':'LICENSE','license_sha256':'47479541ef4e0cef78174f121d2408cd9ea4a9c3182ff2699eb0c002943b23f8',
     'files':[
        ('ricaun.Revit.FileInfo.Tests/Files/2024/Project.rvt','674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'),
        ('ricaun.Revit.FileInfo.Tests/Files/2024/ProjectTemplate.rte','5dfe764e2c47aabb7e55c02d3b1bd53370f38088c8db2af5a68224dd82a79364')]},
    {'repo':'Udaragithub/gbXML2IDF','commit':'3c96129c366b0f732a43458770d04a11c42a1e11',
     'license':'MIT','license_path':'LICENSE','license_sha256':'5a80a43aa0c64e0becb73633cb520236c28620c53aacb8f63293986b55db1eee',
     'files':[('PDS-template_v1.rte','a1c30f3d614ad94bae8989811f3d65ea7e098fa73d8c8ae987d503318378c524')]},
    {'repo':'DynamoDS/DynamoRevit','commit':'49cd43c5c3b21271640ae043b8b77374e4796843',
     'license':'Apache-2.0','license_path':'LICENSE.txt','license_sha256':'ec1fe45049abf566d3e86f51ce815c1fd52de7c3095eeef71f72fb5c144f837d',
     'files':[('test/System/Empty-Metric.rvt','92de856979f5795bed02abe832034a0c1837dcc9af3b0f0a89919eb61b68de3a')]},
]


def fetch(url,path,expected):
    data=path.read_bytes() if path.exists() else urllib.request.urlopen(url,timeout=60).read()
    actual=hashlib.sha256(data).hexdigest()
    if actual!=expected:raise ValueError(f'hash mismatch for {url}')
    if not path.exists():path.write_bytes(data)
    return data


def run(reader,target):
    reader=reader.resolve();target=target.resolve()
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    root=Path(__file__).resolve().parent;local=root/'local';local.mkdir(exist_ok=True)
    reports=[]
    with tempfile.TemporaryDirectory(dir=local) as directory:
        project=Path(directory);(project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-minimal-seed"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target)],check=True)
        for item in SOURCES:
            base=f'https://raw.githubusercontent.com/{item["repo"]}/{item["commit"]}/'
            license_file=root/'results'/('minimal_seed-'+item['repo'].split('/')[0]+'-LICENSE.txt')
            license_data=fetch(base+item['license_path'],license_file,item['license_sha256'])
            for remote,expected in item['files']:
                path=local/('minimal_seed-'+Path(remote).name);data=fetch(base+remote,path,expected)
                inventory=json.loads(subprocess.check_output([str(target/'release/rvt-minimal-seed'),str(path)]))
                reports.append({'file':path.name,'bytes':len(data),'sha256':expected,
                    'source_url':base+remote,'source_commit':item['commit'],'license':item['license'],
                    'license_url':base+item['license_path'],'license_sha256':hashlib.sha256(license_data).hexdigest(),
                    'reader_commit':REV,**inventory})
    return {'candidates':reports,'limits':[
        'Repository-level permissive licenses are pinned; no claim is made about the original Revit subscription edition.',
        'No candidate is mutated and no Autodesk application acceptance is asserted.',
        'Full graph coverage establishes a record inventory, not that all project settings or caches can be changed safely.',
        'Native inventory explicitly rejects unsupported historical versions; a filename containing Empty does not prove emptiness.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/minimal_seed-build');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.target),indent=2))
