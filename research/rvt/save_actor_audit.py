"""Redacted actor-field equality audit; labels do not imply shared semantics."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
import olefile
from ancillary_transitions_xml import leaves
from codec import decode as unpage
from fetch_fixture import FILES,HOLDOUTS
from save_increments import decode as decode_increments
from schema_probe import REV

RUST = r'''
fn main() {
 let args: Vec<String> = std::env::args().collect();
 let info = rvt::basic_file_info::BasicFileInfo::from_bytes(&std::fs::read(&args[1]).unwrap()).unwrap();
 println!("{}", serde_json::to_string(&info.properties).unwrap());
}
'''


def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()


def redacted(value):return {'sha256_utf8':digest(value),'characters':len(value),'empty':not value}


def summarize_actor_values(username,properties,xml_values):
    selected={k:v for k,v in properties.items() if any(w in k.casefold() for w in ('username','author','creator','saved by','savedby'))}
    return {'latest_increment_username':redacted(username),
            'basic_property_names':sorted(properties),
            'basic_actor_properties':{k:{**redacted(v),'equals_latest_increment_username':v==username}
                                      for k,v in sorted(selected.items())},
            'all_basic_properties_equal_latest_username':[k for k,v in sorted(properties.items()) if v==username],
            'xml_author_values':{k:{**redacted(v),'equals_latest_increment_username':v==username,
                'equal_basic_actor_properties':[name for name,value in selected.items() if v==value]}
                for k,v in sorted(xml_values.items())}}


def run(source,target,directory,historical):
    source,target=source.resolve(),target.resolve()
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    fixtures={n:h for _,n,h in FILES};fixtures.update(HOLDOUTS)
    for entry in historical['snapshots']:fixtures[entry['file']]=entry['sha256']
    reports=[]
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        project=Path(tmp);(project/'src').mkdir();(project/'src/main.rs').write_text(RUST)
        (project/'Cargo.toml').write_text('[package]\nname="rvt-save-actor-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target)],check=True)
        for name,expected in fixtures.items():
            path=directory/name
            if path.parent.resolve()!=directory.resolve() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError('fixture mismatch')
            with olefile.OleFileIO(path) as f:
                raw=unpage(f.openstream('Global/DocumentIncrementTable').read())[8:]
                gz=zlib.decompressobj(31);data=gz.decompress(raw)
                if not gz.eof or gz.unconsumed_tail:raise ValueError('invalid increment gzip')
                fields=decode_increments(data)[1];increments=fields['m_increments']
                if not increments:raise ValueError('missing increments')
                username=increments[-1]['m_userName']
                (project/'basic.bin').write_bytes(f.openstream('BasicFileInfo').read())
                props=json.loads(subprocess.check_output([str(target/'release/rvt-save-actor-probe'),str(project/'basic.bin')]))
                if len({p['key'] for p in props})!=len(props):raise ValueError('duplicate BasicFileInfo property')
                properties={p['key']:p['value'] for p in props}
                xml_values={};xml_status='stream_absent'
                if f.exists('ProjectInformation'):
                    with zipfile.ZipFile(io.BytesIO(f.openstream('ProjectInformation').read())) as archive:
                        if len(archive.infolist())!=1:raise ValueError('unsupported ProjectInformation archive entries')
                        root=ET.fromstring(archive.read(archive.infolist()[0]))
                        # Reuse sibling XML leaf traversal; select structural author path, not value patterns.
                        values=leaves(root)
                        xml_values={k:v for k,v in values.items() if '}author[' in k.casefold() or '/author[' in k.casefold() or k.casefold().endswith('/@author')}
                        xml_status='parsed'
                rows=[r['m_userName'] for r in increments]
                reports.append({'file':name,'sha256':expected,'reader_commit':REV,
                    'increment_rows':len(rows),'distinct_increment_usernames':len(set(rows)),
                    'latest_username_occurrences_in_increments':rows.count(username),
                    'increment_array_actor_values_equal':[r['m_userName'] for r in fields['m_localIncrements']]==rows,
                    'project_information_status':xml_status,
                    **summarize_actor_values(username,properties,xml_values)})
    return {'fixtures':reports,'fixture_count':len(reports),
            'actual_actor_values_redacted':True,'actor_semantic_equivalence_inferred':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('directory',type=Path);p.add_argument('historical_provenance',type=Path)
    a=p.parse_args();print(json.dumps(run(a.reader_source,a.target,a.directory,json.loads(a.historical_provenance.read_bytes())),indent=2))
