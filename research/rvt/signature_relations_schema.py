"""Inventory signature-related embedded schema declarations via public rvt-rs.

The selected reader binary's hash/version are recorded. No Autodesk executable
is inspected. Best-effort field parsing cannot establish absence of all hints.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PATTERN=re.compile(r'signatur|crypt|sha256|sha512|ecdsa|ed25519',re.I)


def scan(reader, paths):
    out=[]
    for path in paths:
        schema=json.loads(subprocess.check_output([str(reader.resolve()),str(path),'--json']))
        matches=[c for c in schema['classes'] if PATTERN.search(c['name']) or any(PATTERN.search(f['name']) for f in c['fields'])]
        out.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'parsed_classes':len(schema['classes']),'matching_classes':matches})
    return {'reader_sha256':hashlib.sha256(reader.read_bytes()).hexdigest(),
            'reader_version':subprocess.check_output([str(reader.resolve()),'--version'],text=True).strip(),
            'class_or_field_name_pattern':PATTERN.pattern,'files':out,
            'limitations':['Reader field declarations are best-effort and guessed types are not a wire specification.',
                           'Name-pattern absence does not exclude algorithm hints elsewhere in the file.',
                           'Class version is a serialization version, not a cryptographic algorithm identifier.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader',type=Path,required=True)
    p.add_argument('files',nargs='+',type=Path);a=p.parse_args()
    print(json.dumps(scan(a.reader,a.files),indent=2))
