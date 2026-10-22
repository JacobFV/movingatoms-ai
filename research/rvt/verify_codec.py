"""Corpus round-trip proof for complete page framing, including exact payload lengths."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from pages import GLOBAL, STORED
from codec import decode, encode, decode_final, choose


def verify(path):
    streams = []
    with olefile.OleFileIO(path) as file:
        for parts in file.listdir():
            if not (len(parts)==2 and (parts[0]=='Partitions' or
                    parts[0]=='Global' and parts[1] in GLOBAL or parts==['Formats','Latest'])): continue
            raw = file.openstream(parts).read()
            data = decode(raw)
            if encode(data) != raw: raise ValueError(f'nonidentical canonical round trip: {parts}')
            tail = raw[len(raw)//STORED*STORED:]
            layout = choose(decode_final(tail)) if tail else None
            streams.append({'stream': '/'.join(parts), 'stored_bytes': len(raw), 'payload_bytes': len(data),
                            'full_pages': len(raw)//STORED, 'final_page': bool(tail), 'byte_identical': True,
                            'final_layout': vars(layout) if layout else None})
    return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'streams': streams}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('files', type=Path, nargs='+')
    args = p.parse_args()
    print(json.dumps([verify(f) for f in args.files], indent=2))
