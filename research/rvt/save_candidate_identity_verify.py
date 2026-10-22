"""Bind independent candidate identity evidence and audit all known binary copies."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from schema_probe import REV
from parameter_experiment import SOURCE_SHA
from save_candidate import GUID
from basic_file_info_codec import decode,encode


def verify(directory):
    source=directory/'RE1-Architecture.rvt'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source fixture mismatch')
    with olefile.OleFileIO(source) as f:original=f.openstream('BasicFileInfo').read()
    source_identity=decode(original)
    evidence=json.loads((directory/'save-candidate-identity.json').read_bytes())
    reports=[]
    expected=['save-candidate.rvt']+[f'save-candidate-v{i}.rvt' for i in range(2,6)]
    if [row['file'] for row in evidence]!=expected:raise ValueError('requires all five preserved controls')
    for row in evidence:
        path=directory/row['file'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if row['sha256']!=digest or row['reader_commit']!=REV:raise ValueError('stale independent identity evidence')
        with olefile.OleFileIO(path) as f:raw=f.openstream('BasicFileInfo').read()
        report={'file':path.name,'sha256':digest,'reader_commit':REV,'relationships':row['relationships']}
        try:
            identity=decode(raw)
            valid=identity.increments==86 and identity.guid==str(GUID)
            report.update(binary_and_text_copies_consistent=True,
                          binary_and_text_match_new_increment_and_episode=valid,
                          all_opaque_basic_file_info_bytes_preserved=encode(identity,source_identity.increments,source_identity.guid)==original)
        except ValueError as error:
            report.update(binary_and_text_copies_consistent=False,
                          binary_and_text_match_new_increment_and_episode=False,
                          binary_identity_failure=str(error))
        reports.append(report)
    latest=reports[-1]
    if not all(latest['relationships'].values()) or not latest['binary_and_text_match_new_increment_and_episode'] or not latest['all_opaque_basic_file_info_bytes_preserved']:
        raise ValueError('latest candidate identity contract fails')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    print(json.dumps(verify(p.parse_args().directory),indent=2))
