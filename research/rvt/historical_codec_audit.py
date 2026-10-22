"""Cross-check historical framing without assuming canonical encoder selection."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import olefile
import codec
from pages import is_paged,STORED
from partial_pages import identify


def audit(binary,files):
    reports=[]
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for file in files:
            streams=[]
            with olefile.OleFileIO(file) as f:
                for parts in f.listdir():
                    if not is_paged(parts):continue
                    raw=f.openstream(parts).read();payload=codec.decode(raw)
                    # Unique noncanonical source tails must reproduce using
                    # their detected layout, not the encoder's chosen policy.
                    tail=raw[(len(raw)//STORED)*STORED:]
                    exact=[]
                    if tail:
                        for hit in identify(tail):
                            layout=codec.Layout(hit['lanes'],hit['codeword_bits'],int(hit['generator'],16))
                            try:
                                body=codec.unpack(tail,layout)
                                if codec.encode_final_with_layout(body,layout)==tail:
                                    exact.append({'lanes':layout.lanes,'words':layout.words,'generator':hex(layout.generator),
                                        'payload_bytes':len(body),'encoder_policy_matches':codec.choose(body)==layout})
                            except ValueError:continue
                        if len(exact)!=1:raise ValueError('source final layout not unique')
                    stored,decoded,encoded,decoded_again=[root/n for n in ('stored','decoded','encoded','decoded-again')]
                    for p in (stored,decoded,encoded,decoded_again):p.unlink(missing_ok=True)
                    stored.write_bytes(raw)
                    subprocess.run([str(binary),'decode-stream',str(stored),str(decoded)],check=True)
                    if decoded.read_bytes()!=payload:raise ValueError('Rust/Python payload mismatch')
                    subprocess.run([str(binary),'encode-stream',str(decoded),str(encoded)],check=True)
                    encoded_bytes=encoded.read_bytes()
                    if encoded_bytes!=codec.encode(payload):raise ValueError('encoder policy mismatch')
                    subprocess.run([str(binary),'decode-stream',str(encoded),str(decoded_again)],check=True)
                    if decoded_again.read_bytes()!=payload:raise ValueError('Rust encoded roundtrip failed')
                    streams.append({'stream':'/'.join(parts),'stored_bytes':len(raw),'logical_bytes':len(payload),
                        'source_sha256':hashlib.sha256(raw).hexdigest(),'final_layouts':exact,
                        'both_decoders_agree':True,'source_layout_reproduced_exactly':True,
                        'canonical_encoding_equals_source':encoded_bytes==raw,'both_encoders_agree_and_roundtrip':True})
            inventory=json.loads(subprocess.check_output([str(binary),'verify',str(file)]))
            reports.append({'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                'streams':streams,'rust_inventory':inventory})
    return {'writer_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'files':reports,
        'limits':'Decoder accepts unique valid historical layouts; default encoder policy is not proven to reproduce every historical layout or Autodesk save behavior.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('files',type=Path,nargs='+')
    a=p.parse_args();print(json.dumps(audit(a.binary,a.files),indent=2))
