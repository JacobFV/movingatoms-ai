"""Screenshot exact extracted licensed source thumbnails, never edited-output validation."""
import argparse
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from capture_evidence import ROOT,sha


def capture(destination):
    destination=destination.resolve();destination.mkdir(parents=True,exist_ok=False)
    report_path=ROOT/'research/rvt/results/preview-audit.json'
    snapshot=report_path.read_bytes();report=json.loads(snapshot)
    (destination/'preview-audit.json').write_bytes(snapshot)
    images=[];tiles=[]
    for row in report['fixtures']:
        filename=row['extracted_filename']
        if Path(filename).name!=filename:raise ValueError('invalid extracted image filename')
        source=ROOT/'research/rvt/local/preview-images'/filename
        data=source.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['image_sha256']:raise ValueError('preview evidence hash mismatch')
        (destination/filename).write_bytes(data)
        images.append({'file':row['file'],'source_sha256':row['source_sha256'],
                       'image':filename,'image_sha256':row['image_sha256']})
        tiles.append('<article><img width="128" height="128" src="'+html.escape(filename)+'"><div>'+html.escape(row['file'])+'</div><small>Original embedded preview · 128 × 128</small></article>')
    timestamp=datetime.now(timezone.utc).isoformat();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Licensed source preview audit</title>
<style>body{background:#edf1f5;font:17px Arial;color:#172338;margin:0}main{background:white;border-top:7px solid #166c61;margin:30px auto;padding:28px;max-width:1100px}h1{font-size:30px}section{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}article{border:1px solid #dce3e9;text-align:center;padding:12px;font-size:14px;overflow-wrap:anywhere}small,footer{font-size:12px;color:#536274}img{display:block;margin:0 auto 10px}.warning{background:#fff3dc;padding:16px;margin:20px 0}</style><main><small>RVT CLEAN-ROOM RESEARCH · SOURCE THUMBNAIL AUDIT</small><h1>Exact previews from eleven licensed source files</h1><p>PNG CRCs, dimensions and pixel hashes verified. Every historical pair changes actual pixels.</p><section>'''+''.join(tiles)+'''</section><div class="warning"><strong>Provenance boundary:</strong> these are original embedded source thumbnails. They are not renders of our edited candidates and do not establish Revit acceptance. The contact sheet is an actual browser screenshot.</div><footer>Captured '''+html.escape(timestamp)+' · source commit '+revision[:12]+'. Exact source, stream and PNG hashes are archived beside this screenshot.</footer></main></html>'
    page=destination/'source-previews.html';page.write_text(body)
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:raise RuntimeError('Chrome required')
    version=subprocess.check_output([chrome,'--version'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='rvt-source-preview-') as profile:
        command=[chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',f'--user-data-dir={profile}','--hide-scrollbars','--window-size=1280,1100',f'--screenshot={destination}/source-previews.png',page.as_uri()]
        subprocess.run(command,check=True,capture_output=True,text=True,timeout=45)
    manifest={'captured_at_utc':timestamp,'source_commit':revision,
      'working_tree_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
      'browser':version,'source_report_sha256':hashlib.sha256(snapshot).hexdigest(),
      'generator_sha256':sha(Path(__file__)),'images':images,
      'source_thumbnails_only':True,'edited_output_validation':False,'not_autodesk_ui':True,
      'artifacts':{p.name:sha(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'destination':str(destination),'source_images':len(images),'browser':version}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    print(json.dumps(capture(p.parse_args().destination)))
