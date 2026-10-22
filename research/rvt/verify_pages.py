"""Verify every eligible stream and reproduce all stored bytes with the encoder."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from pages import GLOBAL, STORED
from paged import decode, encode


def verify(path):
    streams = []
    with olefile.OleFileIO(path) as ole:
        for parts in ole.listdir():
            if not (len(parts) == 2 and (parts[0] == 'Partitions' or
                    parts[0] == 'Global' and parts[1] in GLOBAL or
                    parts == ['Formats', 'Latest'])):
                continue
            raw = ole.openstream(parts).read()
            clean = decode(raw)
            if encode(clean) != raw:
                raise ValueError(f'nonidentical reconstruction: {parts}')
            streams.append({'name': '/'.join(parts), 'stored_bytes': len(raw),
                            'full_pages': len(raw)//STORED, 'byte_identical': True})
    return {'file_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'generator': 'x^11+x^2+1', 'interleaved_lanes': 255,
            'full_pages_verified': sum(s['full_pages'] for s in streams),
            'streams': streams, 'revit_openability': 'not_tested'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    print(json.dumps([verify(p) for p in args.files], indent=2))
