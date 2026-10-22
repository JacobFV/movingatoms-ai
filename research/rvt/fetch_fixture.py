"""Fetch SHA-256-pinned MIT test models, never proprietary/education fixtures."""
import hashlib
from pathlib import Path
import urllib.request

REV = 'fd755e18cec40ed016d06b082f420d796571fef1'
BASE = f'https://media.githubusercontent.com/media/magnetar-io/revit-test-datasets/{REV}/Revit/'
FILES = [
    ('2024_Core_Interior.rvt', 'core2024.rvt', 'c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'),
    ('Revit_IFC5_Einhoven.rvt', 'einhoven.rvt', 'd3a0c6d37d3f47a1726bc5aa7fe3880ed3c13bbe819b5e64680f6710b15aa948'),
]

if __name__ == '__main__':
    dest = Path(__file__).parent / 'local'
    dest.mkdir(exist_ok=True)
    for remote, local, expected in FILES:
        target = dest / local
        data = target.read_bytes() if target.exists() else urllib.request.urlopen(BASE + remote, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'fixture checksum mismatch: {remote}')
        if not target.exists(): target.write_bytes(data)
        print(f'{target}: verified {expected}')
