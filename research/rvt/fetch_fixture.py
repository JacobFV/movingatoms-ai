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

HOLDOUT_REV = '9e8b37175a0fba1397f7011aeee917fe52de7623'
HOLDOUT_BASE = f'https://raw.githubusercontent.com/Drshelden/IFC-ECS/{HOLDOUT_REV}/data/RE1/'
HOLDOUTS = [
    ('RE1-Architecture.rvt', '4a78bdd68e7f4dd7806060db07c222da9a810e20b3f303c17a443294b91c8ce4'),
    ('RE1-Mechanical.rvt', 'd559720177aa0ec435133f804e7c45d60da2deb9d5585bb3d55f4830139c014b'),
    ('RE1-Plumbing.rvt', '03689df2aa426031a216e65051b9f19d3265d6fe96884dd47373b17435f9e54c'),
    ('RE1-Electrical.rvt', '9875e765c9f47893808c47b845a8379b8777b92510e3e0284f763cb457c9630b'),
]

if __name__ == '__main__':
    dest = Path(__file__).parent / 'local'
    dest.mkdir(exist_ok=True)
    for base, remote, local, expected in ([(BASE, r, l, h) for r,l,h in FILES] +
                                         [(HOLDOUT_BASE, n, n, h) for n,h in HOLDOUTS]):
        target = dest / local
        data = target.read_bytes() if target.exists() else urllib.request.urlopen(base + remote, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'fixture checksum mismatch: {remote}')
        if not target.exists(): target.write_bytes(data)
        print(f'{target}: verified {expected}')
