"""Verify newly recognized Contents page framing in both language codecs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import olefile
from codec import decode,encode
from pages import is_paged


def verify(binary,files):
    reports=[]
    if not is_paged(['Contents']):raise ValueError('Contents omitted from page classification')
    with tempfile.TemporaryDirectory() as temp:
        for index,path in enumerate(files):
            root=Path(temp)/str(index);root.mkdir()
            with olefile.OleFileIO(path) as f:stored=f.openstream('Contents').read()
            logical=decode(stored)
            if encode(logical)!=stored:raise ValueError('Contents Python encoding differs')
            (root/'stored').write_bytes(stored)
            subprocess.run([str(binary),'decode-stream',str(root/'stored'),str(root/'logical')],check=True)
            if (root/'logical').read_bytes()!=logical:raise ValueError('Rust/Python Contents payload differs')
            subprocess.run([str(binary),'encode-stream',str(root/'logical'),str(root/'encoded')],check=True)
            if (root/'encoded').read_bytes()!=stored:raise ValueError('Rust Contents encoding differs')
            inventory=json.loads(subprocess.check_output([str(binary),'verify',str(path)]))
            reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'contents_stored_bytes':len(stored),'contents_logical_bytes':len(logical),
                            'both_codecs_reproduce_contents_exactly':True,'rust_inventory':inventory})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path)
    p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps(verify(a.binary,a.files),indent=2))
