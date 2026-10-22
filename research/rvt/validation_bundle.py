"""Create concrete Autodesk-validation candidates plus independent-reader evidence.

No upload occurs. Reports always leave Autodesk acceptance as not_tested.
Use the pinned Core fixture and pinned public rvt-rs binaries documented here.
"""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import uuid
from episode_experiment import make as episode
from transport_experiment import make as transport


def sha(data): return hashlib.sha256(data).hexdigest()

def canonical_ifc(data):
    data,n=re.subn(rb"(FILE_NAME\('[^']*',)'[^']*'",rb"\1'<export time>'",data)
    if n!=1: raise ValueError('expected exactly one IFC FILE_NAME timestamp')
    data,n=re.subn(rb'(IFCOWNERHISTORY\([^;]*,)[0-9]+\);',rb'\1<export time>);',data)
    if n!=1: raise ValueError('expected exactly one IFCOWNERHISTORY timestamp')
    return data


def make(source, dest, writer, elements, ifc):
    dest.mkdir(parents=True,exist_ok=False)
    base_elements=subprocess.check_output([elements,str(source)])
    subprocess.run([ifc,str(source),'-o',str(dest/'original.ifc')],check=True)
    base_ifc=(dest/'original.ifc').read_bytes()
    original_sha=sha(source.read_bytes())
    reports=[]
    for mode in ['identity','gzip-mtime','episode']:
        plan=dest/(mode+'-plan')
        if mode=='episode':
            detail=episode(source,plan,uuid.UUID('f9a1ea5c-5989-4af8-8b24-c0d54bb1fd51'))
        else:
            with contextlib.redirect_stdout(io.StringIO()) as capture: transport(source,plan,mode)
            detail=json.loads(capture.getvalue())
        output=dest/(mode+'.rvt')
        result=json.loads(subprocess.check_output([writer,'patch',str(source),str(output),str(plan/'manifest.json')]))
        data=subprocess.check_output([elements,str(output)])
        if data!=base_elements: raise ValueError(f'{mode}: element projection changed')
        subprocess.run([ifc,str(output),'-o',str(dest/(mode+'.ifc'))],check=True)
        exported=(dest/(mode+'.ifc')).read_bytes()
        if canonical_ifc(exported)!=canonical_ifc(base_ifc): raise ValueError(f'{mode}: IFC projection changed')
        if mode=='identity' and result['output_sha256']!=original_sha: raise ValueError('identity differs')
        reports.append({'case':mode,'experiment':detail,'writer':result,
                        'element_json_sha256':sha(data),'element_json_byte_identical':True,
                        'ifc_byte_identical':exported==base_ifc,
                        'ifc_equal_except_export_timestamps':True,
                        'ifc_canonical_sha256':sha(canonical_ifc(exported)),
                        'autodesk_acceptance':'not_tested'})
    report={'source_sha256':original_sha,'cases':reports,
            'tool_sha256':{name:sha(Path(path).read_bytes()) for name,path in [('writer',writer),('elements',elements),('ifc',ifc)]},
            'ifc_normalization':['FILE_NAME timestamp','IFCOWNERHISTORY creation timestamp'],
            'native_element_creation_tested':False,'complete_save_transaction_tested':False}
    (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (dest/'VALIDATE.txt').write_text('''Open the original licensed Core Interior model first as a control.
Then open identity.rvt, gzip-mtime.rvt, and episode.rvt separately in Autodesk
Viewer or Revit. Record the exact file SHA-256, Autodesk product/build, result,
warnings, and whether model contents match the original. A Viewer conversion
success establishes only that conversion; it is not proof of editable native
elements or a valid Revit save transaction. Revit open/save/reopen is a distinct
check. None of these cases adds model elements. Do not mark unsupported checks
as passed. The source fixture revision/license is in fetch_fixture.py.
''')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('dest',type=Path)
    p.add_argument('--writer',required=True)
    p.add_argument('--elements',required=True)
    p.add_argument('--ifc',required=True)
    a=p.parse_args()
    make(a.source,a.dest,a.writer,a.elements,a.ifc)
