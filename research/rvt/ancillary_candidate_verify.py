"""Audit ancillary variants against preserved prior candidate controls."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
import save_increments
from project_information_codec import patch_timestamp


def streams(path):
    with olefile.OleFileIO(path)as f:return {'/'.join(n):f.openstream(n).read()for n in f.listdir()}


def verify(source,control,candidate,identity_evidence):
    original,old,new=map(streams,(source,control,candidate))
    if old.keys()!=new.keys():raise ValueError('ancillary variant changes stream inventory')
    changed=[name for name in old if old[name]!=new[name]]
    if set(changed)!={'ProjectInformation','Contents','Global/DocumentIncrementTable'}:
        raise ValueError('ancillary variant changed unexpected streams')
    def increments(data):return save_increments.decode(unpack_global(unpage(data))[0])[1]
    previous=increments(old['Global/DocumentIncrementTable']);revised=increments(new['Global/DocumentIncrementTable'])
    sourcefields=increments(original['Global/DocumentIncrementTable'])
    if any(f['m_increments'][-1]['m_atimeStamp']['m_msb'] != 0 for f in (sourcefields,previous,revised)):
        raise ValueError('unsupported high timestamp word')
    from copy import deepcopy
    expected=deepcopy(previous)
    keys=('contentDocuments','transmissionData','projectXMLInfo')
    for array in ('m_increments','m_localIncrements'):
        for key in keys:expected[array][-1][f'm_{key}StreamRevision']=sourcefields[array][-1][f'm_{key}StreamRevision']+1
    if expected!=revised:raise ValueError('increment arrays differ beyond explicit policy')
    if previous['m_increments'][-1]['m_atimeStamp']!=revised['m_increments'][-1]['m_atimeStamp']:
        raise ValueError('control/variant save timestamp differs')
    expectedproject,projectevidence=patch_timestamp(original['ProjectInformation'],hashlib.sha256(original['ProjectInformation']).hexdigest(),
        sourcefields['m_increments'][-1]['m_atimeStamp']['m_lsb'],revised['m_increments'][-1]['m_atimeStamp']['m_lsb'])
    if expectedproject!=new['ProjectInformation']:raise ValueError('ProjectInformation differs from guarded source-bound edit')
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    matching=[r for r in identity_evidence if r['sha256']==digest]
    if len(matching)!=1 or not all(matching[0]['relationships'].values()):raise ValueError('missing/mismatched independent save identity audit')
    revisions={key:revised['m_increments'][-1][f'm_{key}StreamRevision']for key in save_increments.REVISIONS}
    return {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'control_sha256':hashlib.sha256(control.read_bytes()).hexdigest(),'candidate_sha256':digest,
            'changed_streams_from_control':sorted(changed),'all_other_control_streams_byte_identical':True,
            'latest_revisions':revisions,'independent_identity_relationships':matching[0]['relationships'],
            'project_information':projectevidence,'preview_revision_and_bytes_retained':True,
            'limitations':['Preview retained without regeneration; no equal-payload historical preview pair establishes this choice.',
                          'Historical regular-counter convention is evidence, not a complete native save specification.',
                          'Signatures and Autodesk acceptance remain unresolved.'],
            'complete_save_transaction':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','control','candidate','identity_evidence'):p.add_argument(n,type=Path)
    a=p.parse_args();print(json.dumps(verify(a.source,a.control,a.candidate,json.loads(a.identity_evidence.read_bytes())),indent=2))
