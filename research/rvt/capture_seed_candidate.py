"""Capture actual independently triangulated geometry from a verified seed run."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def capture(run_directory, destination):
    raws = {n: (run_directory / (n + '.json')).read_bytes() for n in ('run', 'native', 'ifc')}
    run, native, ifc = (json.loads(raws[n]) for n in ('run', 'native', 'ifc'))
    if run['status'] != 'verified_research_candidate':
        raise ValueError('successful verified research run required')
    candidate = run['candidate_sha256']
    for n, report in (('native', native), ('ifc', ifc)):
        if report['candidate_sha256'] != candidate or hashlib.sha256(raws[n]).hexdigest() != run['validation_reports'][n + '.json']:
            raise ValueError('report does not bind the verified candidate')
    walls = ifc['walls']
    if len(walls) != 3 or not native['only_requested_physical_elements_projected']:
        raise ValueError('three-wall minimal document capture required')
    specs = {r['id']: r for r in native['records'] if 'spec' in r}
    if {w['id'] for w in walls} != set(specs):
        raise ValueError('native and IFC wall inventories differ')
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in raws.items():
        (destination / (name + '.json')).write_bytes(raw)
    shared = np.max([np.ptp(np.array(w['vertices_metres']), axis=0) for w in walls], axis=0) + [.4, .5, .2]
    fig = plt.figure(figsize=(12, 4.8), layout='constrained')
    for i, wall in enumerate(walls):
        points = np.asarray(wall['vertices_metres'], float)
        faces = np.asarray(wall['triangles'], int)
        if points.shape != (8, 3) or faces.shape != (12, 3) or not np.isfinite(points).all():
            raise ValueError('unexpected mesh arrays')
        ax = fig.add_subplot(1, 3, i + 1, projection='3d')
        ax.add_collection3d(Poly3DCollection(points[faces], facecolors=['#217d95', '#168c7a', '#9c6e2f'][i], edgecolors='#26384a', linewidths=.6, alpha=.85))
        center = (points.max(axis=0) + points.min(axis=0)) / 2
        ax.set_xlim(center[0] - shared[0]/2, center[0] + shared[0]/2)
        ax.set_ylim(center[1] - shared[1]/2, center[1] + shared[1]/2)
        ax.set_zlim(center[2] - shared[2]/2, center[2] + shared[2]/2)
        ax.set_box_aspect(shared.copy())
        ax.view_init(elev=18, azim=-65)
        ax.set_yticks([round(float(center[1]), 2)])
        ax.set_xlabel('World X (m)', fontsize=8)
        ax.set_zlabel('Z (m)', fontsize=8)
        ax.tick_params(labelsize=7)
        spec = specs[wall['id']]['spec']
        ax.set_title(f"ID {wall['id']} · {spec['length_feet']:g} × {spec.get('height_feet',15):g} ft", fontsize=11)
    fig.savefig(destination / 'meshes.png', dpi=150)
    plt.close(fig)
    timestamp = datetime.now(timezone.utc).isoformat()
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    rows = ''.join(f'<tr><td>{w["id"]}</td><td>{w["closed_volume_cubic_metres"]:.6f} m³</td><td>{len(w["vertices_metres"])} / {len(w["triangles"])}</td></tr>' for w in walls)
    body = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Minimal-seed native candidate evidence</title><style>body{background:#edf1f5;color:#172338;font:18px Arial;margin:0}main{background:white;max-width:1160px;margin:28px auto;padding:28px;border-top:7px solid #166c61}h1{font-size:30px}.cards{display:flex;gap:16px}.card{flex:1;background:#eef7f5;padding:16px}.big{display:block;font-size:28px}td,th{text-align:left;padding:10px;border-bottom:1px solid #d9e1e6}table{width:100%;border-collapse:collapse}.notice{background:#fff3dc;padding:16px;margin:18px 0}pre{font-size:12px;white-space:pre-wrap}footer{font-size:12px;color:#536274}</style><main><small>RVT CLEAN-ROOM RESEARCH · ACTUAL SAVED GEOMETRY</small><h1>Three new walls in a minimal native project</h1>'''
    body += f'<div class="cards"><div class="card"><b class="big">{native["prior_identities_preserved"]:,}</b>seed scaffold identities preserved</div><div class="card"><b class="big">0 → 3</b>projected physical elements</div><div class="card"><b class="big">200 mm</b>existing seed wall type</div></div>'
    body += '<img style="width:100%" src="meshes.png" alt="Actual independently triangulated saved wall geometry">'
    body += '<table><tr><th>Native wall ID</th><th>Independent IFC solid volume</th><th>Vertices / triangles</th></tr>' + rows + '</table>'
    body += '<p>The writer adds an upper level and three walls, remaps dependencies to the seed, and preserves the original partition. Independent checks verify native BRep geometry, level constraints, reference closure and the three measured registration lists. The plots use actual IFC mesh arrays exported from the saved RVT.</p>'
    body += '<div class="notice"><strong>Validation boundary:</strong> local research checks pass. This is a generated evidence-report screenshot, not Revit UI. Native regeneration, opening and re-saving remain untested. IFC schema validation uses explicit OwnerHistory correction controls.</div>'
    body += '<pre>Candidate SHA-256: ' + html.escape(candidate) + '</pre>'
    body += f'<footer>Captured {timestamp} · commit {revision[:12]}. Full reports and actual mesh arrays are archived with artifact hashes.</footer></main></html>'
    page = destination / 'candidate.html'
    page.write_text(body)
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:
        raise RuntimeError('Chrome required')
    with tempfile.TemporaryDirectory(prefix='rvt-seed-candidate-') as profile:
        subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking', '--no-first-run', f'--user-data-dir={profile}', '--hide-scrollbars', '--window-size=1340,1300', f'--screenshot={destination}/candidate.png', page.as_uri()], check=True, capture_output=True, timeout=45)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {'captured_at_utc': timestamp, 'source_commit': revision,
                'working_tree_status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True),
                'browser': subprocess.check_output([chrome, '--version'], text=True).strip(),
                'matplotlib_version': matplotlib.__version__, 'numpy_version': np.__version__,
                'generator_sha256': sha(Path(__file__)), 'not_autodesk_ui': True, 'actual_ifc_meshes': True,
                'source_report_sha256': {n: hashlib.sha256(raw).hexdigest() for n, raw in raws.items()},
                'artifacts': {p.name: sha(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run_directory', type=Path)
    p.add_argument('destination', type=Path)
    a = p.parse_args()
    capture(a.run_directory, a.destination)
