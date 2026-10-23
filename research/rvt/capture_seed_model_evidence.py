"""Chrome evidence capture from a fully verified combined seed-model run.

Plots only independently read-back native mesh arrays. Requested geometry is
never used as a drawing input. Report and candidate hashes are mandatory.
"""
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


def esc(value):
    return html.escape(str(value))


def capture(run_directory, destination):
    run_directory = run_directory.resolve()
    run_path = run_directory / 'run.json'
    run = json.loads(run_path.read_bytes())
    if run['status'] != 'verified_research_candidate':
        raise ValueError('fully verified final pipeline run required')
    candidate = run['candidate_sha256']
    if sha(run_directory / 'verified-candidate.rvt') != candidate:
        raise ValueError('verified candidate hash mismatch')
    reports = {}
    for name, expected in run['validation_reports'].items():
        if Path(name).name != name or not name.endswith('.json'):
            raise ValueError('unsafe report filename')
        if sha(run_directory / name) != expected:
            raise ValueError('report hash mismatch: ' + name)
        reports[name] = json.loads((run_directory / name).read_bytes())
    native, metadata = reports['native.json'], reports['metadata.json']
    if native['candidate_sha256'] != candidate or metadata['candidate_sha256'] != candidate:
        raise ValueError('reports bind a different candidate')
    if not metadata['table']['all_source_rows_byte_identical']:
        raise ValueError('source preservation verification missing')
    elements, levels = native['elements'], native['levels']
    if not elements:
        raise ValueError('empty verified element inventory')
    meshes = []
    for element in elements:
        if not element['application_properties_exact'] or not element['oriented_triangles_exact_after_SI_to_feet_float32'] or set(element['channels']) != {'101', '102', '103'}:
            raise ValueError('incomplete native verification')
        for channel, record in element['channels'].items():
            if record['sha256'] != metadata['body_sha256'][channel][str(element['element_id'])]:
                raise ValueError('channel body binding mismatch')
        count = 0
        for index, primitive in enumerate(element['meshes']):
            points = np.asarray(primitive['vertices'], float) * .3048
            normals = np.asarray(primitive['normals'], float)
            triangles = np.asarray(primitive['triangles'], int)
            if points.ndim != 2 or points.shape[1] != 3 or normals.shape != points.shape or triangles.ndim != 2 or triangles.shape[1] != 3 or not np.isfinite(points).all() or not np.isfinite(normals).all() or triangles.min() < 0 or triangles.max() >= len(points):
                raise ValueError('invalid saved mesh arrays')
            material = element['render_materials'][str(index)]
            color = material['base_color']
            if len(color) != 4 or not all(0 <= c <= 1 for c in color):
                raise ValueError('invalid saved viewport color')
            meshes.append({'element_id': element['element_id'], 'application_id': element['application_id'], 'vertices_metres': points.tolist(), 'normals': normals.tolist(), 'triangles': triangles.tolist(), 'material': material, 'render_style_id': primitive['render_style_id']})
            count += len(triangles)
        if count != element['triangle_count']:
            raise ValueError('saved triangle count mismatch')
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for path in [run_path, *(run_directory / name for name in reports)]:
        shutil.copyfile(path, destination / path.name)
    (destination / 'mesh-metres.json').write_text(json.dumps(meshes, indent=2, ensure_ascii=False) + '\n')
    points = np.concatenate([m['vertices_metres'] for m in meshes])
    low, high = points.min(axis=0), points.max(axis=0)
    center, span = (low+high)/2, np.maximum(high-low, .1)*1.15
    fig = plt.figure(figsize=(12, 5), layout='constrained')
    for index, azimuth in enumerate((-65, 35)):
        ax = fig.add_subplot(1, 2, index+1, projection='3d')
        for mesh in meshes:
            vertices, triangles = np.asarray(mesh['vertices_metres']), np.asarray(mesh['triangles'])
            ax.add_collection3d(Poly3DCollection(vertices[triangles], facecolors=mesh['material']['base_color'], edgecolors='#30343a', linewidths=.35))
        for axis, dimension in zip(('x', 'y', 'z'), range(3)):
            getattr(ax, 'set_'+axis+'lim')(center[dimension]-span[dimension]/2, center[dimension]+span[dimension]/2)
            getattr(ax, 'set_'+axis+'ticks')(np.linspace(low[dimension], high[dimension], 3).round(2))
            getattr(ax, 'set_'+axis+'label')(axis.upper()+' (m)')
        ax.set_box_aspect(span)
        ax.view_init(elev=22, azim=azimuth)
        ax.tick_params(labelsize=8)
        ax.set_title('Actual saved scene · view '+str(index+1))
    fig.savefig(destination/'scene.png', dpi=150)
    plt.close(fig)
    stamp = datetime.now(timezone.utc).isoformat()
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    body = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Combined seed model evidence</title><style>body{margin:0;background:#edf1f5;color:#172338;font:16px Arial}main{max-width:1180px;margin:22px auto;padding:24px;background:white;border-top:7px solid #166c61}h1{font-size:29px}.cards{display:flex;gap:14px}.card{flex:1;padding:12px;background:#eef5f3}.big{display:block;font-size:26px}table{width:100%;border-collapse:collapse}td,th{padding:8px;text-align:left;vertical-align:top;border-bottom:1px solid #dae2e7}pre{font-size:12px;white-space:pre-wrap;margin:0;overflow-wrap:anywhere}.notice{background:#fff1d7;padding:14px;margin:14px 0}footer{font-size:12px;color:#526172}.props{max-width:530px}</style><main><small>CLEAN-ROOM RVT RESEARCH · LOCAL TECHNICAL REPORT</small><h1>Combined native model: saved geometry and application data</h1>'''
    triangles = sum(len(m['triangles']) for m in meshes)
    body += f'<div class="cards"><div class="card"><b class="big">{len(elements)} owners</b>{len(meshes)} saved mesh primitives</div><div class="card"><b class="big">{triangles} triangles</b>read back from verified RVT</div><div class="card"><b class="big">{metadata["table"]["source_rows"]:,} source rows</b>byte-identical preservation</div></div><img src="scene.png" style="width:100%" alt="All saved mesh components rendered from verified native read-back">'
    body += '<p>Actual native saved vertices and triangles; feet converted to metres (× 0.3048). Each primitive uses its decoded source-style viewport RGBA. Normals are archived unchanged. Colors are reader viewport interpretations, not Autodesk rendering.</p>'
    body += '<table><tr><th>Named level / native ID</th><th>Elevation</th><th>Application ID</th></tr>'
    for level in levels:
        body += f'<tr><td>{esc(level["name"])} / {level["element_id"]}</td><td>{level["elevation_m"]:g} m</td><td>{esc(level["id"])}</td></tr>'
    body += '</table><table><tr><th>Saved owner</th><th>Category / level relationship</th><th>Exact application properties</th></tr>'
    for element in elements:
        relation = element['application_level_relationship']
        name = 'none' if relation is None else relation['name']
        props = json.dumps(element['metadata_properties']['application_properties'], ensure_ascii=False, sort_keys=True, indent=2)
        body += f'<tr><td><b>{esc(element["name"])}</b><br>{esc(element["application_id"])} · native {element["element_id"]}<br>{element["triangle_count"]} triangles · channels 101/102/103</td><td>{esc(element["category"])}<br>Application level: {esc(name)}<br>Native associated-level: {element["native_associated_level_id"]}</td><td class="props"><pre>{esc(props)}</pre></td></tr>'
    body += '</table><div class="notice"><b>Evidence boundary:</b> Chrome screenshot of a generated local report, not Autodesk UI. Options, lifecycle defaults and DirectShape category-registration policy remain hypotheses. Named levels are native elements; requested element-to-level relationships and application properties are stored in our own extensible-storage schema. Native associated-level remains unset (-1). Autodesk opening, regeneration and re-saving are untested. Ordinary public IFC export skips DirectShape.</div>'
    body += f'<pre>Verified candidate SHA-256: {candidate}\nNative report SHA-256: {run["validation_reports"]["native.json"]}</pre><footer>Captured {stamp} · commit {revision[:12]}. Reports, actual mesh arrays, material provenance, browser and generator hashes archived.</footer></main></html>'
    page = destination/'model.html'
    page.write_text(body)
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:
        raise RuntimeError('Chrome required')
    height = 1120 + 110*len(elements) + 35*len(levels)
    with tempfile.TemporaryDirectory(prefix='rvt-seed-model-browser-') as profile:
        subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking', '--no-first-run', f'--user-data-dir={profile}', '--hide-scrollbars', f'--window-size=1380,{height}', f'--screenshot={destination}/model.png', page.as_uri()], check=True, capture_output=True, timeout=45)
    manifest = {'captured_at_utc':stamp,'source_commit':revision,'source_run':str(run_directory),'candidate_sha256':candidate,'working_tree_status':subprocess.check_output(['git','status','--short'],cwd=root,text=True),'browser':subprocess.check_output([chrome,'--version'],text=True).strip(),'matplotlib_version':matplotlib.__version__,'numpy_version':np.__version__,'generator_sha256':sha(Path(__file__)),'not_autodesk_ui':True,'actual_native_saved_meshes':True,'ordinary_ifc_export':False,'source_report_sha256':{p.name:sha(p) for p in [run_path,*(run_directory/name for name in reports)]},'artifacts':{p.name:sha(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    capture(args.run_directory,args.destination)
