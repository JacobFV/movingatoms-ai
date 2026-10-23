"""Capture the archived minimal-seed inventory as a local evidence report."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def capture(report, output):
    raw = report.read_bytes()
    values = json.loads(raw)
    seed = next(c for c in values['candidates'] if c['file'] == 'minimal_seed-Project.rvt')
    summary = seed['summary']
    if not seed['all_current_graphs_complete'] or summary['unsupported_graph_records']:
        raise ValueError('incomplete seed inventory')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'inventory.json').write_bytes(raw)
    rows = ''.join('<tr><td>' + html.escape(name) + '</td><td>' + str(summary['classes'].get(name, {}).get('records', 0)) + '</td></tr>'
                   for name in ('Level', 'BasicWallType', 'MaterialElem', 'SWall', 'FamilyInstance', 'DirectShape'))
    timestamp = datetime.now(timezone.utc).isoformat()
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    body = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Minimal RVT seed evidence</title>
<style>body{background:#edf1f5;color:#172338;font:19px Arial;margin:0}main{background:white;max-width:1080px;margin:28px auto;padding:30px;border-top:7px solid #166c61}h1{font-size:34px}.cards{display:flex;gap:16px}.card{flex:1;background:#eef7f5;padding:18px}.big{display:block;font-size:32px}td,th{text-align:left;padding:10px;border-bottom:1px solid #d9e1e6}table{width:100%;border-collapse:collapse}.notice{background:#fff3dc;padding:18px;margin-top:20px}pre{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}footer{font-size:13px;color:#536274}</style><main>
<small>RVT CLEAN-ROOM RESEARCH · ARCHIVED NATIVE RECORD INVENTORY</small>
<h1>A minimal project without donor building instances</h1>'''
    body += f'<div class="cards"><div class="card"><b class="big">{seed["bytes"]:,} bytes</b>Revit 2024 project</div><div class="card"><b class="big">{summary["indexed_elements"]:,}</b>scaffold elements</div><div class="card"><b class="big">{summary["complete_graph_records"]:,}</b>complete record graphs</div></div>'
    body += '<p>Published MIT fixture: ricaun.Revit.FileInfo / Files/2024/Project.rvt. All indexed current records decode completely; none use an off-route fallback.</p>'
    body += '<table><tr><th>Selected class</th><th>Decoded records across channels</th></tr>' + rows + '</table>'
    body += '<p>The project retains built-in settings, types, materials, a level and view scaffolding. The complete class inventory and pinned license provenance are archived in inventory.json.</p>'
    body += '<div class="notice"><strong>Validation boundary:</strong> this is an inventory of an unchanged source file, not a newly generated model. Schema/reference remapping and save bookkeeping are subsequent implementation work. This local report screenshot is not Revit UI and does not establish Autodesk acceptance of edited files.</div>'
    body += '<pre>Fixture SHA-256: ' + html.escape(seed['sha256']) + '\nPublic reader commit: ' + html.escape(seed['reader_commit']) + '</pre>'
    body += f'<footer>Captured {timestamp} · repository commit {revision[:12]}. Source JSON is a previously recorded audit, not a new decode during screenshot capture.</footer></main></html>'
    page = output / 'seed.html'
    page.write_text(body)
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:
        raise RuntimeError('Chrome required')
    with tempfile.TemporaryDirectory(prefix='rvt-seed-browser-') as profile:
        subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking', '--no-first-run', f'--user-data-dir={profile}', '--hide-scrollbars', '--window-size=1240,1100', f'--screenshot={output}/seed.png', page.as_uri()], check=True, capture_output=True, timeout=45)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {'captured_at_utc': timestamp, 'source_commit': revision,
                'working_tree_status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True),
                'browser': subprocess.check_output([chrome, '--version'], text=True).strip(),
                'generator_sha256': digest(Path(__file__)), 'not_autodesk_ui': True,
                'source_report_sha256': hashlib.sha256(raw).hexdigest(),
                'artifacts': {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    capture(args.report, args.destination)
