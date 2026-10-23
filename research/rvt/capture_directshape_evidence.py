"""Capture a Chrome report of hash-bound native saved DirectShape mesh arrays."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(run_directory, destination):
    names = ('run', 'native', 'metadata', 'scene')
    raws = {n: (run_directory / (n + '.json')).read_bytes() for n in names}
    run, native, metadata, scene = (json.loads(raws[n]) for n in names)
    if run['status'] != 'verified_research_candidate':
        raise ValueError('verified research run required')
    candidate = run['candidate_sha256']
    if sha(run_directory / 'verified-candidate.rvt') != candidate:
        raise ValueError('candidate hash mismatch')
    for n in ('native', 'metadata', 'scene'):
        if hashlib.sha256(raws[n]).hexdigest() != run['validation_reports'][n + '.json']:
            raise ValueError('report hash mismatch: ' + n)
    if any(r['candidate_sha256'] != candidate for r in (native, metadata)):
        raise ValueError('candidate report mismatch')
    if native['saved_scene_sha256'] != run['validation_reports']['scene.json']:
        raise ValueError('native scene hash mismatch')
    if not (native['native_channels_complete'] and native['rendered_triangles_match_request_after_float32'] and metadata['table']['all_source_rows_byte_identical']):
        raise ValueError('required verification missing')
    records = scene['records']
    owner = native['new_element_id']
    if {r['channel'] for r in records} != {101, 102, 103} or len(records) != 3:
        raise ValueError('expected complete three-channel owner')
    for r in records:
        if r['identity']['element_id'] != owner or r['status'] != 'complete_bounded_graph' or r['source']['body_sha256'] != metadata['body_sha256'][str(r['channel'])][str(owner)]:
            raise ValueError('record binding mismatch')
    saved = scene['scene']
    if saved['units'] != 'feet' or len(saved['elements']) != 1 or saved['elements'][0]['id'] != owner:
        raise ValueError('unexpected scene units or owner inventory')
    element = saved['elements'][0]
    if element['status'] != 'decoded_saved_graphics':
        raise ValueError('saved graphics required')
    geometry = []
    for i, primitive in enumerate(element['meshes']['primitives']):
        points = np.asarray(primitive['vertices'], float) * .3048
        normals = np.asarray(primitive['normals'], float)
        faces = np.asarray(primitive['triangles'], int)
        if points.ndim != 2 or points.shape[1] != 3 or normals.shape != points.shape or faces.ndim != 2 or faces.shape[1] != 3 or not np.isfinite(points).all() or not np.isfinite(normals).all() or faces.min() < 0 or faces.max() >= len(points):
            raise ValueError('invalid mesh arrays')
        cross = np.cross(points[faces[:, 1]] - points[faces[:, 0]], points[faces[:, 2]] - points[faces[:, 0]])
        if not np.all(np.sum(cross * normals[faces[:, 0]], axis=1) > 0):
            raise ValueError('saved normals disagree with winding')
        color = element['render_materials'][str(i)]['base_color']
        geometry.append({'vertices_metres': points.tolist(), 'normals': normals.tolist(), 'triangles': faces.tolist(), 'base_color': color})
    if sum(len(g['triangles']) for g in geometry) != native['rendered_triangle_count'] or sum(len(g['vertices_metres']) for g in geometry) != native['rendered_vertices']:
        raise ValueError('native mesh totals mismatch')
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for n, raw in raws.items():
        (destination / (n + '.json')).write_bytes(raw)
    (destination / 'mesh-metres.json').write_text(json.dumps(geometry, indent=2) + '\n')
    fig = plt.figure(figsize=(11, 4.4), layout='constrained')
    all_points = np.concatenate([g['vertices_metres'] for g in geometry])
    bounds = [all_points.min(axis=0), all_points.max(axis=0)]
    center = (bounds[0] + bounds[1]) / 2
    span = (bounds[1] - bounds[0]) * 1.2
    for i, azim in enumerate((-60, 35)):
        ax = fig.add_subplot(1, 2, i + 1, projection='3d')
        for g in geometry:
            points, faces = np.asarray(g['vertices_metres']), np.asarray(g['triangles'])
            ax.add_collection3d(Poly3DCollection(points[faces], facecolors=g['base_color'], edgecolors='#222222', linewidths=.7))
        ax.set_xlim(center[0]-span[0]/2, center[0]+span[0]/2)
        ax.set_ylim(center[1]-span[1]/2, center[1]+span[1]/2)
        ax.set_zlim(center[2]-span[2]/2, center[2]+span[2]/2)
        ax.set_xticks(np.linspace(bounds[0][0], bounds[1][0], 3).round(2))
        ax.set_yticks(np.linspace(bounds[0][1], bounds[1][1], 3).round(2))
        ax.set_zticks(np.linspace(bounds[0][2], bounds[1][2], 4).round(2))
        ax.set_box_aspect(span)
        ax.view_init(elev=20, azim=azim)
        ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
        ax.set_title('Saved native mesh · view ' + str(i+1))
        ax.tick_params(labelsize=8)
    fig.savefig(destination / 'mesh.png', dpi=150)
    plt.close(fig)
    stamp = datetime.now(timezone.utc).isoformat()
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    rows = ''.join(f'<tr><td>{r["channel"]}</td><td>{html.escape(r["class_name"])}</td><td>{r["source"]["body_bytes"]} bytes</td><td>Complete bounded graph</td></tr>' for r in records)
    body = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Saved DirectShape mesh evidence</title><style>body{margin:0;background:#edf1f5;color:#172338;font:17px Arial}main{max-width:1160px;margin:24px auto;background:white;padding:26px;border-top:7px solid #166c61}h1{font-size:30px}.cards{display:flex;gap:14px}.card{flex:1;background:#eef5f3;padding:14px}.big{display:block;font-size:27px}table{width:100%;border-collapse:collapse}td,th{padding:8px;text-align:left;border-bottom:1px solid #dce3e8}.notice{background:#fff1d7;padding:14px;margin-top:16px}pre{font-size:12px;white-space:pre-wrap}footer{font-size:12px;color:#526172}</style><main><small>CLEAN-ROOM RVT RESEARCH · LOCAL TECHNICAL REPORT</small><h1>New DirectShape: geometry read back from saved RVT</h1>'''
    body += f'<div class="cards"><div class="card"><b class="big">Owner {owner}</b>three native channels</div><div class="card"><b class="big">{native["rendered_vertices"]} / {native["rendered_triangle_count"]}</b>saved vertices / triangles</div><div class="card"><b class="big">{metadata["table"]["source_rows"]:,}</b>source table rows byte-identical</div></div>'
    body += '<img src="mesh.png" style="width:100%" alt="Two views of actual saved native mesh"><table><tr><th>Channel</th><th>Root class</th><th>Body length</th><th>Read-back status</th></tr>' + rows + '</table>'
    body += '<p>Actual scene.json vertices, normals and triangle indices; coordinates converted from feet to metres (× 0.3048). Triangle winding agrees with saved normals. Gray RGBA (0.498039, 0.498039, 0.498039, 1) is the reader’s initialized default viewport material, not a serialized material-property claim.</p>'
    body += '<div class="notice"><b>Evidence boundary:</b> This is a Chrome screenshot of a generated local technical report, not Autodesk UI. DirectShape options, lifecycle defaults and the unchanged Global / no-registration policy remain hypotheses. Autodesk opening, regeneration and re-saving are untested. This is not ordinary IFC export: the public exporter skips DirectShape.</div>'
    body += '<pre>Verified candidate SHA-256: ' + candidate + '\nScene report SHA-256: ' + run['validation_reports']['scene.json'] + '</pre>'
    body += f'<footer>Captured {stamp} · source commit {revision[:12]} · full reports, arrays, generator and artifact hashes archived.</footer></main></html>'
    page = destination / 'directshape.html'
    page.write_text(body)
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:
        raise RuntimeError('Chrome required')
    with tempfile.TemporaryDirectory(prefix='rvt-directshape-browser-') as profile:
        subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking', '--no-first-run', f'--user-data-dir={profile}', '--hide-scrollbars', '--window-size=1340,1270', f'--screenshot={destination}/directshape.png', page.as_uri()], check=True, capture_output=True, timeout=45)
    manifest = {'captured_at_utc': stamp, 'source_commit': revision, 'source_run': str(run_directory), 'candidate_sha256': candidate, 'working_tree_status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True), 'browser': subprocess.check_output([chrome, '--version'], text=True).strip(), 'matplotlib_version': matplotlib.__version__, 'numpy_version': np.__version__, 'generator_sha256': sha(Path(__file__)), 'not_autodesk_ui': True, 'actual_native_saved_scene': True, 'ordinary_ifc_export': False, 'source_report_sha256': {n: hashlib.sha256(raw).hexdigest() for n, raw in raws.items()}, 'artifacts': {p.name: sha(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    capture(args.run_directory, args.destination)
