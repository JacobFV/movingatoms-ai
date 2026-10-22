"""Package verified, prebuilt signature experiments for external validation.

No upload or Autodesk result is implied. Includes the licensed original as a
control. Fails if artifacts do not match their writer reports or reader data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from parameter_experiment import SOURCE_SHA
from validation_bundle import canonical_ifc
from verify_parameter_experiment import verify as verify_room

MODES=['recompress-control','footer-control','unsigned-control','room-finish','unsigned-room-finish']
LICENSE_SHA='12d75062332fe0087934ce6660684e92601c9d385fe730f967dd2c4797530ec6'
README='''RVT signature validation candidates — research, not production outputs

The original is MIT-licensed RE1 Architecture from Drshelden/IFC-ECS revision
9e8b37175a0fba1397f7011aeee917fe52de7623 (license included).
No proprietary Revit/ODA implementation was examined. report.json records
exact file hashes and independent-reader comparisons, not Autodesk results.

Run these separately in the same Autodesk product/build:
1. original.rvt: establish that the untouched fixture opens.
2. recompress-control.rvt: identical model bytes; one gzip member recompressed.
3. footer-control.rvt: identical model bytes; one private-signature bit flipped.
   This is deliberately an invalid-integrity control, not a proposed model.
4. unsigned-control.rvt: identical model bytes; the base content group's
   private/public signature fields are empty. This representation occurs in
   source files, but acceptance for nonempty content is unproven.
5. room-finish.rvt: room 348738 (Storage Narrow, RE-9) Floor Finish changes
   Wood -> Cork; Adler-32/gzip/page framing updated, signature preserved.
6. unsigned-room-finish.rvt: same room edit, with that group's signature fields
   cleared. All other groups and streams retain their original content.

Record SHA-256, Autodesk product/build, success/failure, and exact warnings.
In Revit, inspect the room's Floor Finish, save to a new path, close and reopen.
Record those outcomes separately. Viewer conversion success alone does not
establish valid editable models or Revit save/reopen behavior. All candidates
leave save/History bookkeeping unchanged and create no new elements.
If the original fails, the other outcomes cannot isolate our changes.
No outcome proves the signature algorithm or keying by itself.
'''


def sha(data):return hashlib.sha256(data).hexdigest()

def bundle(root,output):
    research=Path(__file__).resolve().parent
    original=(root/'RE1-Architecture.rvt').read_bytes()
    if sha(original)!=SOURCE_SHA:raise ValueError('original fixture hash mismatch')
    license=(research/'licenses/IFC-ECS-MIT.txt').read_bytes()
    if sha(license)!=LICENSE_SHA:raise ValueError('fixture license hash mismatch')
    room=verify_room(root)
    model_before=(root/'architecture-elements.json').read_bytes()
    model_after=(root/'room-finish-elements.json').read_bytes()
    ifc_before=canonical_ifc((root/'architecture-original.ifc').read_bytes())
    ifc_after=canonical_ifc((root/'room-finish.ifc').read_bytes())
    cases=[];artifacts={'original.rvt':original,'LICENSE.txt':license,'VALIDATE.txt':README.encode()}
    for mode in MODES:
        data=(root/(mode+'.rvt')).read_bytes()
        report=json.loads((research/'results'/f'{mode}-writer.json').read_text())
        if sha(data)!=report['output_sha256'] or report['input_sha256']!=SOURCE_SHA:
            raise ValueError(f'{mode} writer hash mismatch')
        edited=mode in ('room-finish','unsigned-room-finish')
        projected=(root/(mode+'-elements.json')).read_bytes()
        if projected!=(model_after if edited else model_before):raise ValueError(f'{mode} element mismatch')
        projected_ifc=canonical_ifc((root/(mode+'.ifc')).read_bytes())
        if projected_ifc!=(ifc_after if edited else ifc_before):raise ValueError(f'{mode} IFC mismatch')
        cases.append({'case':mode,'sha256':sha(data),'expected_room_finish':'Cork' if edited else 'Wood',
                      'reader_elements_match_expected':True,'ifc_matches_expected_except_export_timestamps':True,
                      'autodesk_open':'not_tested','autodesk_save_reopen':'not_tested'})
        artifacts[mode+'.rvt']=data
    result={'original_sha256':SOURCE_SHA,'license_sha256':LICENSE_SHA,
            'reader_revision':room['reader_commit'],'cases':cases,
            'new_element_creation':False,'save_bookkeeping_updated':False,
            'signature_algorithm':'unknown','autodesk_enforcement':'not_tested'}
    artifacts['report.json']=(json.dumps(result,indent=2)+'\n').encode()
    # Exclusive creation prevents overwriting prior validation evidence.
    with output.open('xb')as target:
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED)as archive:
            for name,data in artifacts.items():archive.writestr(name,data)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(bundle(a.directory,a.output),indent=2))
