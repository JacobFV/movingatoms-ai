"""Capture actual browser screenshots of local research reports, with provenance.

These are screenshots of generated evidence pages, never Autodesk/Revit UI.
No network requests, fixture binaries or account credentials are needed.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCES=('object-repacking','resized-graph','resized-reader','record-selection')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def esc(value):return html.escape(str(value))


def capture(dest,chrome):
    dest=dest.resolve();dest.mkdir(parents=True,exist_ok=False)
    timestamp=datetime.now(timezone.utc).isoformat()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    sources={};values={}
    for name in SOURCES:
        path=ROOT/'research/rvt/results'/f'{name}.json'
        sources[str(path.relative_to(ROOT))]=sha(path)
        values[name]=json.loads(path.read_bytes())
        shutil.copyfile(path,dest/path.name)
    test_command=['python3','-m','unittest','discover','-s','research/rvt','-p','test_*.py']
    test=subprocess.run(test_command,cwd=ROOT,capture_output=True,text=True)
    log=test.stdout+test.stderr;(dest/'tests.txt').write_text(log)
    corpus=values['object-repacking'];graph=values['resized-graph'];edit=values['resized-reader']
    routing=values['record-selection']
    style='''body{margin:0;background:#edf1f5;color:#172338;font:19px Arial,sans-serif}main{max-width:1100px;margin:35px auto;padding:35px;background:white;border-top:7px solid #166c61}h1{font-size:34px;margin:12px 0 22px}h2{font-size:23px}small,.label{font-size:14px;color:#536274}table{border-collapse:collapse;width:100%;font-size:17px}td,th{padding:11px;border-bottom:1px solid #dce3e9;text-align:left}.cards{display:flex;gap:20px;margin:20px 0}.card{flex:1;background:#eef7f5;padding:20px}.number{font-size:34px;font-weight:bold}.warning{background:#fff3dc;padding:17px;margin-top:25px}pre{font:15px monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#eef1f5;padding:16px}footer{font-size:13px;color:#536274;margin-top:24px;overflow-wrap:anywhere}'''
    common=f'<div class="label">RVT CLEAN-ROOM RESEARCH · LOCAL EVIDENCE REPORT</div><small>Captured {esc(timestamp)} · source commit {revision[:12]}</small>'
    warning='<div class="warning"><strong>Acceptance boundary:</strong> no Autodesk open/save test. Signature generation, complete save transactions and new-element creation remain unresolved. This is not a Revit screenshot.</div>'
    rows=''.join(f'<tr><td>{esc(r["file"])}</td><td>{r["object_records"]:,}</td><td>{r["content_groups"]}</td><td>Exact record bodies</td></tr>' for r in corpus)
    summary=common+'<h1>Object reconstruction across six licensed files</h1>'+f'<div class="cards"><div class="card"><div class="number">{sum(x["object_records"] for x in corpus):,}</div>records repacked</div><div class="card"><div class="number">{sum(x["content_groups"] for x in corpus):,}</div>content groups</div><div class="card"><div class="number">{sum(x["exact_episode_routes"] for x in routing):,}</div>exact revision routes</div></div>'+'<table><tr><th>Fixture</th><th>Records</th><th>Groups</th><th>Recorded result</th></tr>'+rows+'</table>'+f'<p>Additional selection evidence: {sum(x["unique_compaction_history_holders"] for x in routing)} unique compaction-history holders; {sum(x["sole_holders_with_unresolved_history"] for x in routing)} sole holders with unexplained history.</p>'+warning
    changed=common+f'<h1>Real room edit: {esc(edit["old"])} → {esc(edit["new"])}</h1><p>RE1 Architecture · room {edit["changed_element"]} · {esc(edit["changed_field"])}</p>'+f'<div class="cards"><div class="card"><div class="number">+{graph["body_growth_bytes"]}</div>serialized bytes</div><div class="card"><div class="number">{graph["complete_objects"]}</div>complete graph objects</div><div class="card"><div class="number">{graph["resolved_pointer_edges"]}</div>resolved pointer edges</div></div>'+f'<p>Independent reader: one changed property among {edit["element_count"]} exported elements. All other graph values and pointer targets preserved.</p><h2>Independent IFC before / after</h2><pre>{esc(edit["ifc_before_line"])}\n{esc(edit["ifc_after_line"])}</pre><h2>Fresh Python regression run · exit {test.returncode}</h2><pre>{esc(log[-1400:])}</pre>'+warning
    browser_version=subprocess.check_output([chrome,'--version'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='rvt-evidence-browser-') as profile:
        for name,body in [('corpus',summary),('room-edit',changed)]:
            page=dest/f'{name}.html';page.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>RVT research evidence</title><style>'+style+'</style><main>'+body+f'<footer>Source JSON copies and SHA-256 provenance are stored beside this capture. Browser: {esc(browser_version)}.</footer></main></html>')
            args=[chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',f'--user-data-dir={profile}','--hide-scrollbars','--window-size=1280,1100',f'--screenshot={dest/name}.png',page.as_uri()]
            subprocess.run(args,check=True,capture_output=True,text=True,timeout=45)
    artifacts={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()}
    manifest={'captured_at_utc':timestamp,'source_commit':revision,'working_tree_status':status,
              'browser':browser_version,'capture_type':'actual headless-browser screenshot of local generated research report',
              'not_autodesk_ui':True,'sources':sources,'test_command':test_command,'test_exit_code':test.returncode,
              'generator_sha256':sha(Path(__file__)),'artifacts':artifacts}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if test.returncode:raise RuntimeError('regression tests failed; evidence retained')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--chrome',default=shutil.which('google-chrome') or shutil.which('chromium'))
    a=p.parse_args()
    if not a.chrome:p.error('Chrome/Chromium executable required')
    result=capture(a.destination,a.chrome)
    print(json.dumps({'captured_at_utc':result['captured_at_utc'],'test_exit_code':result['test_exit_code'],'artifacts':list(result['artifacts'])}))
