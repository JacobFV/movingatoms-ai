"""Audit adjacent snapshots from the separately verified provenance manifest."""
import argparse
import json
from pathlib import Path
from paired_modification import compare, read_snapshot


def run(manifest, directory):
    snapshots = []
    for item in manifest['snapshots']:
        path = directory/item['file']
        if path.parent.resolve() != directory.resolve(): raise ValueError('invalid snapshot path')
        snapshots.append(read_snapshot(path,item['sha256']))
    return {'provenance_report':'paired-save-sources.json',
            'pairs':[compare(before,after) for before,after in zip(snapshots,snapshots[1:])],
            'controlled_edit_sequence':False,'autodesk_save_rules_inferred':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('directory',type=Path)
    a=p.parse_args();print(json.dumps(run(json.loads(a.manifest.read_bytes()),a.directory),indent=2))
