"""Classify IFC effects of the fresh non-geometric DataStorage candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from ifc_identity_audit import RUST,differences
from schema_probe import REV
from new_element_experiment import SOURCE_SHA


def run(reader,target,source,candidate,dest,identity_evidence):
    reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source fixture mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    matches=[r for r in identity_evidence if r['sha256']==SOURCE_SHA]
    if len(matches)!=1:raise ValueError('source namespace evidence mismatch')
    namespace=matches[0]['document_guid'];dest.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(dir=dest)as tmp:
        work=Path(tmp);(work/'src').mkdir();(work/'src/main.rs').write_text(RUST)
        (work/'Cargo.toml').write_text('[package]\nname="rvt-create-ifc-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        reports=[]
        for label,path in [('source',source),('candidate',candidate)]:
            data=json.loads(subprocess.check_output([str(target/'release/rvt-create-ifc-probe'),str(path),str(dest/label),namespace]))
            reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**data})
    default=differences(dest/'source-default.ifc',dest/'candidate-default.ifc')
    stable=differences(dest/'source-stable.ifc',dest/'candidate-stable.ifc')
    if stable['identifier_change_count'] or stable['other_changes']:raise ValueError('DataStorage unexpectedly changes stable IFC projection')
    if default['other_changes']:raise ValueError('default IFC differs beyond generated identifiers')
    return {'reader_commit':REV,'exports':reports,'default_projection':default,'stable_namespace_projection':stable,
            'stable_namespace_ifc_byte_identical':(dest/'source-stable.ifc').read_bytes()==(dest/'candidate-stable.ifc').read_bytes(),
            'limitation':'DataStorage has no IFC geometry projection; unchanged IFC alone does not validate new RVT element registration.',
            'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('dest',type=Path)
    p.add_argument('--identity-evidence',type=Path,default=Path(__file__).parent/'results/save-identity.json');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.target,a.source,a.candidate,a.dest,json.loads(a.identity_evidence.read_bytes())),indent=2))
