"""Isolate save-GUID-dependent IFC identifiers and test an explicit stable namespace.

This uses the pinned public reader through its public IfcModel API; no source
patches or rewritten IFC text. The caller owns namespace persistence/uniqueness.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import uuid
from schema_probe import REV
from validation_bundle import canonical_ifc

RUST = r'''
fn main() -> Result<(),Box<dyn std::error::Error>> {
    use rvt::ifc::RvtDocExporter;
    use rvt::ifc::step_writer::{write_step_with_options,StepOptions};
    use std::io::Write;
    let a:Vec<String>=std::env::args().collect();
    let mut file=rvt::RevitFile::open(std::path::Path::new(&a[1]))?;
    let result=RvtDocExporter.export_with_diagnostics(&mut file)?;
    let mut model=result.model;
    let options=StepOptions{timestamp:Some(1792627200)};
    let original=model.global_ids.clone();
    let write=|suffix:&str,data:String|->Result<(),Box<dyn std::error::Error>> {
        let mut output=std::fs::OpenOptions::new().write(true).create_new(true)
            .open(format!("{}{}",a[2],suffix))?;
        output.write_all(data.as_bytes())?; Ok(())
    };
    write("-default.ifc",write_step_with_options(&model,&options))?;
    model.global_ids.document=Some(a[3].clone());
    write("-stable.ifc",write_step_with_options(&model,&options))?;
    let mut expected=original.clone();expected.document=Some(a[3].clone());
    assert_eq!(expected,model.global_ids);
    println!("{}",serde_json::json!({"default_namespace":original.document,
        "explicit_namespace":a[3],"native_element_ids":original.elements.len(),
        "native_storey_ids":original.storeys.len(),"native_type_ids":original.types.len(),
        "all_native_ids_preserved":true}));
    Ok(())
}
'''


def differences(left,right):
    before=canonical_ifc(left.read_bytes()).splitlines()
    after=canonical_ifc(right.read_bytes()).splitlines()
    if len(before)!=len(after):raise ValueError('IFC line count differs')
    pattern=re.compile(rb"^(#\d+=([A-Z0-9]+)\(')([0-3][0-9A-Za-z_$]{21})('.*)$")
    ids=Counter();others=[]
    for a,b in zip(before,after):
        if a==b:continue
        x,y=pattern.match(a),pattern.match(b)
        if x and y and x[1]==y[1] and x[4]==y[4]:ids[x[2].decode()]+=1
        else:others.append({'before':a.decode(),'after':b.decode()})
    return {'line_count':len(before),'identifier_changes':dict(ids),
            'identifier_change_count':sum(ids.values()),'other_changes':others}


def run(reader,target,source,candidate,dest,namespace):
    reader=reader.resolve();target=target.resolve()
    namespace=str(uuid.UUID(namespace))
    if namespace==str(uuid.UUID(int=0)):raise ValueError('namespace must be nonzero')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    dest.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(dir=dest) as tmp:
        project=Path(tmp);(project/'src').mkdir();(project/'src/main.rs').write_text(RUST)
        (project/'Cargo.toml').write_text('[package]\nname="rvt-ifc-identity-audit"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target)],check=True)
        exports=[]
        for label,path in [('source',source),('candidate',candidate)]:
            result=json.loads(subprocess.check_output([str(target/'release/rvt-ifc-identity-audit'),str(path),str(dest/label),namespace]))
            exports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**result})
    if exports[0]['default_namespace']!=namespace:
        raise ValueError('this control requires retaining the source export namespace')
    if (dest/'source-default.ifc').read_bytes()!=(dest/'source-stable.ifc').read_bytes():
        raise ValueError('explicit source namespace unexpectedly changes source export')
    default=differences(dest/'source-default.ifc',dest/'candidate-default.ifc')
    stable=differences(dest/'source-stable.ifc',dest/'candidate-stable.ifc')
    if stable['identifier_change_count'] or len(stable['other_changes'])!=2:
        raise ValueError('stable namespace fails controlled candidate contract')
    replacements=[("IFCTEXT('Partitions/80')","IFCTEXT('Partitions/85')"),
                  ("IFCLABEL('Wood')","IFCLABEL('Polished concrete')")]
    for row,(old,new) in zip(stable['other_changes'],replacements):
        if old not in row['before'] or row['before'].replace(old,new)!=row['after']:
            raise ValueError('unexpected stable-projection content change')
    if default['other_changes']!=stable['other_changes']:
        raise ValueError('namespace changes affect more than generated identifiers')
    return {'reader_commit':REV,'exports':exports,'default_projection':default,
            'explicit_stable_namespace_projection':stable,
            'source_export_byte_identical':True,'native_ids_preserved':True,
            'rust_adapter_sha256':hashlib.sha256(RUST.encode()).hexdigest(),
            'policy':'Caller supplies and persistently owns the original export namespace; no automatic document identity inference.',
            'autodesk_acceptance':'not_tested','complete_native_export':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--namespace',required=True);p.add_argument('source',type=Path)
    p.add_argument('candidate',type=Path);p.add_argument('dest',type=Path)
    a=p.parse_args();print(json.dumps(run(a.reader_source,a.target,a.source,a.candidate,a.dest,a.namespace),indent=2))
