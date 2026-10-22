"""Locate newest History episode GUID encodings; read-only, not a reference decoder."""
import argparse
import hashlib
import json
from pathlib import Path
import uuid
import zlib
import olefile
from codec import decode as unpage
from pages import is_paged
from save_history import decode as history_decode
from save_candidate import unpack_global


def occurrences(data, needle):
    start=0
    while True:
        offset=data.find(needle,start)
        if offset<0:return
        yield offset
        start=offset+1


def scan(files):
    reports=[]
    for path in files:
        with olefile.OleFileIO(path) as f:
            history=history_decode(unpack_global(unpage(f.openstream('Global/History').read()))[0])
            # Codec stores episodes as GUID/strength pairs.
            guid=uuid.UUID(bytes_le=history.episodes[0][:16])
            needles={'uuid_le':guid.bytes_le,'uuid_be':guid.bytes,
                     'utf8':str(guid).encode(),'utf16le':str(guid).encode('utf-16-le')}
            hits=[]; members=0; streams=0
            for parts in f.listdir():
                streams+=1
                data=f.openstream(parts).read()
                if is_paged(parts):data=unpage(data)
                domains=[('logical',None,data)]
                for offset in occurrences(data,b'\x1f\x8b\x08\x00'):
                    try:
                        d=zlib.decompressobj(31);raw=d.decompress(data[offset:])
                        if not d.eof or d.unconsumed_tail:continue
                    except zlib.error:continue
                    members+=1;domains.append(('gzip',offset,raw))
                for domain,base,raw in domains:
                    for encoding,needle in needles.items():
                        offsets=list(occurrences(raw,needle))
                        if offsets:hits.append({'stream':'/'.join(parts),'domain':domain,
                            'gzip_logical_offset':base,'encoding':encoding,'offsets':offsets})
            reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'newest_episode_guid':str(guid),'streams_scanned':streams,'gzip_members_scanned':members,'hits':hits,
                'limits':'Exact common UUID encodings in logical streams and valid gzip members only. No semantic reference claim; alternate encodings and other compression are not covered.'})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',nargs='+',type=Path)
    print(json.dumps(scan(p.parse_args().files),indent=2))
