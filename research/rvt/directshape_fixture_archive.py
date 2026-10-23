"""Fetch the license-pinned Dynamo Primer DirectShape exercise model (Revit 2015)."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

REV='388bb962bd38e3d77b747d0a84013a49c285e261'
BASE=f'https://raw.githubusercontent.com/DynamoDS/DynamoPrimerNew/{REV}/'
ARCHIVE_SHA='5b43c6fbe3a71a486fb7b3316710cc280b81c88413314cfc72a7cf8f56e7f143'
MODEL_SHA='6e76a717f970333f417a59751354a3a43d68288cf4e0c9bcaa729d9b63ac41f2'
LICENSE_SHA='4f8429c9c2dafb7f29b752249dbbf873b560d7c8ddd9067a1f9ee90e82634f43'


def check(data,expected):
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('fixture hash mismatch')
    return data


def fetch(directory):
    directory.mkdir(parents=True,exist_ok=True)
    license_path=directory/'DynamoPrimer-LICENSE.txt'
    license_data=check(license_path.read_bytes() if license_path.exists() else urllib.request.urlopen(BASE+'LICENSE').read(),LICENSE_SHA)
    target=directory/'primer-ARCH-DirectShape-BaseFile.rvt'
    if target.exists():check(target.read_bytes(),MODEL_SHA)
    else:
        archive=check(urllib.request.urlopen(BASE+'.gitbook/assets/Revit-Creating-DirectShape.zip').read(),ARCHIVE_SHA)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            data=check(z.read('ARCH-DirectShape-BaseFile.rvt'),MODEL_SHA)
        target.write_bytes(data)
    if not license_path.exists():license_path.write_bytes(license_data)
    return target

if __name__=='__main__':print(fetch(Path(__file__).parent/'local/directshape-fixtures'))
