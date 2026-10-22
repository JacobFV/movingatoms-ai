"""Test unclassified streams for exact recovered page framing; no auto-classification."""
import argparse
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode,encode
from pages import is_paged


def audit(files):
    reports=[]
    for path in files:
        streams=[]
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if is_paged(parts):continue
                raw=f.openstream(parts).read()
                row={'stream':'/'.join(parts),'stored_bytes':len(raw),
                     'sha256':hashlib.sha256(raw).hexdigest()}
                try:
                    logical=decode(raw)
                    row['page_round_trip']=encode(logical)==raw
                    row['decoded_bytes']=len(logical)
                except ValueError as error:
                    row['page_round_trip']=False
                    row['page_codec_rejection']=str(error)
                streams.append(row)
        reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'unclassified_streams':streams,
                        'interpretation':'Exact page-codec trial only; not a semantic parser or checksum audit.'})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',type=Path,nargs='+')
    print(json.dumps(audit(p.parse_args().files),indent=2))
