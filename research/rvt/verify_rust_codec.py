"""Cross-language corpus oracle: Rust decoding/encoding must equal Python and source."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
import olefile
from pages import is_paged
from codec import decode


def verify(binary, source):
    checked = 0
    with tempfile.TemporaryDirectory() as tmp, olefile.OleFileIO(source) as file:
        root = Path(tmp)
        for parts in file.listdir():
            if not is_paged(parts): continue
            raw = file.openstream(parts).read()
            stored, payload, encoded = [root/f'{checked}-{n}' for n in ('stored','payload','encoded')]
            stored.write_bytes(raw)
            subprocess.run([binary,'decode-stream',str(stored),str(payload)],check=True)
            if payload.read_bytes()!=decode(raw): raise ValueError(f'payload mismatch: {source} {parts}')
            subprocess.run([binary,'encode-stream',str(payload),str(encoded)],check=True)
            if encoded.read_bytes()!=raw: raise ValueError(f'encoding mismatch: {source} {parts}')
            checked += 1
    result = json.loads(subprocess.check_output([binary,'verify',str(source)]))
    return {'file':source.name, 'streams_cross_checked':checked, 'rust_report':result}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary')
    p.add_argument('files',type=Path,nargs='+')
    a=p.parse_args()
    print(json.dumps([verify(a.binary,f) for f in a.files],indent=2))
