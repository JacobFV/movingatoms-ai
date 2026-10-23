"""Fetch two license-pinned fixture candidates; neither qualifies as a 2024 instance."""
from pathlib import Path
import hashlib
import json
import urllib.request

FIXTURES=[
 {'repository':'DynamoDS/DynamoRevit','commit':'49cd43c5c3b21271640ae043b8b77374e4796843',
  'path':'test/System/DirectShape/singleDirectShape.rvt','name':'singleDirectShape.rvt',
  'sha256':'3b05630eb71230b567b891f7829a9a6326b435b002b99d571d3830790fe50431',
  'license_path':'LICENSE.txt','license_name':'DynamoRevit-LICENSE.txt',
  'license_sha256':'ec1fe45049abf566d3e86f51ce815c1fd52de7c3095eeef71f72fb5c144f837d','license':'Apache-2.0'},
 {'repository':'ricaun-io/ricaun.Revit.FileInfo','commit':'9228ef12063fd294a565c47b989449ab93460a61',
  'path':'ricaun.Revit.FileInfo.Tests/Files/2024/Project.rvt','name':'ricaun-Project2024.rvt',
  'sha256':'674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe',
  'license_path':'LICENSE','license_name':'ricaun-LICENSE.txt',
  'license_sha256':'47479541ef4e0cef78174f121d2408cd9ea4a9c3182ff2699eb0c002943b23f8','license':'MIT'}]


def fetch(directory):
    directory.mkdir(parents=True,exist_ok=True)
    for f in FIXTURES:
        base=f"https://raw.githubusercontent.com/{f['repository']}/{f['commit']}/"
        for path,name,sha in [(f['license_path'],f['license_name'],f['license_sha256']),
                              (f['path'],f['name'],f['sha256'])]:
            target=directory/name
            data=target.read_bytes() if target.exists() else urllib.request.urlopen(base+path).read()
            if hashlib.sha256(data).hexdigest()!=sha:raise ValueError(f'hash mismatch: {name}')
            if not target.exists():target.write_bytes(data)
    return FIXTURES

if __name__=='__main__':
    print(json.dumps(fetch(Path(__file__).parent/'local/directshape-fixtures'),indent=2))
