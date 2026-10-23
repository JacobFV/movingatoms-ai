"""Capture a verified local batch experiment with genuine IFC mesh plots."""
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

ROOT = Path(__file__).resolve().parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(run_dir, output):
    values={};raws={}
    for name in ('run','native','metadata','ifc','meshes'):
        raws[name]=(run_dir/(name+'.json')).read_bytes();values[name]=json.loads(raws[name])
    run=values['run'];native=values['native'];ifc=values['ifc'];evidence=values['meshes']
    if run['status']!='verified_research_candidate':raise ValueError('run has not passed all checks')
    candidate=run['candidate_sha256']
    if any(values[n]['candidate_sha256']!=candidate for n in ('native','metadata','ifc')):raise ValueError('candidate bindings differ')
    for name in ('native','metadata','ifc'):
        if hashlib.sha256(raws[name]).hexdigest()!=run['validation_reports'][name+'.json']:raise ValueError('report changed since verification')
    if evidence['native_candidate_sha256']!=candidate or hashlib.sha256(raws['meshes']).hexdigest()!=ifc['mesh_evidence_sha256']:raise ValueError('mesh evidence binding differs')
    if evidence['units']!='metres' or evidence['coordinates']!='world':raise ValueError('unsupported coordinate convention')
    meshes=[m for m in evidence['meshes'] if m['label']=='new']
    if len(meshes)<3 or [m['native_element_id'] for m in meshes]!=run['new_element_ids']:raise ValueError('capture requires at least three verified walls')
    total_walls=len(meshes);meshes=meshes[:3]
    output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    for name,raw in raws.items():(output/(name+'.json')).write_bytes(raw)
    shared=np.max([np.ptp(np.array(m['vertices']),axis=0) for m in meshes],axis=0)+[.4,.5,.2]
    fig=plt.figure(figsize=(12,4.5),layout='constrained');measurements=[]
    for index,mesh in enumerate(meshes):
        vertices=np.asarray(mesh['vertices'],float);triangles=np.asarray(mesh['triangles'],int)
        if vertices.shape!=(8,3) or triangles.shape!=(12,3) or not np.isfinite(vertices).all():raise ValueError('unexpected mesh')
        low=vertices.min(axis=0);high=vertices.max(axis=0);center=(low+high)/2
        ax=fig.add_subplot(1,3,index+1,projection='3d')
        ax.add_collection3d(Poly3DCollection(vertices[triangles],facecolors=['#217d95','#168c7a','#9c6e2f'][index],edgecolors='#26384a',linewidths=.6,alpha=.85))
        ax.set_xlim(center[0]-shared[0]/2,center[0]+shared[0]/2);ax.set_ylim(center[1]-shared[1]/2,center[1]+shared[1]/2);ax.set_zlim(center[2]-shared[2]/2,center[2]+shared[2]/2)
        ax.set_box_aspect(shared.copy());ax.view_init(elev=18,azim=-65);ax.set_yticks([round(float(center[1]),2)])
        ax.set_xlabel('World X (m)',fontsize=8);ax.set_zlabel('Z (m)',fontsize=8);ax.tick_params(labelsize=7)
        row=native['walls'][index];length=row['spec']['length_feet']
        ax.set_title(f"{length:g} ft · ID {mesh['native_element_id']}",fontsize=12)
        measurements.append({'id':mesh['native_element_id'],'minimum_metres':low.tolist(),'maximum_metres':high.tolist(),'native_volume_cubic_feet':row['native_brep']['closed_solid_volume_cubic_feet']})
    fig.savefig(output/'meshes.png',dpi=150);fig.savefig(output/'meshes.svg');plt.close(fig)
    # Normalize Matplotlib's trailing SVG spaces before hashing/capture.
    svg=output/'meshes.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    (output/'measurements.json').write_text(json.dumps(measurements,indent=2)+'\n')
    rows=''.join(f'<tr><td>{w["spec"]["element_id"]}</td><td>{w["spec"]["length_feet"]:g} ft</td><td>{w["native_brep"]["closed_solid_volume_cubic_feet"]:.6f} ft³</td><td>6 / 12 / 8</td></tr>' for w in native['walls'][:3])
    timestamp=datetime.now(timezone.utc).isoformat();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Native wall batch evidence</title><style>body{background:#edf1f5;color:#172338;font:18px Arial;margin:0}main{background:white;max-width:1160px;margin:28px auto;padding:28px;border-top:7px solid #166c61}h1{font-size:30px}.cards{display:flex;gap:16px}.card{flex:1;background:#eef7f5;padding:16px}strong.big{display:block;font-size:27px}table{border-collapse:collapse;width:100%;font-size:17px}td,th{text-align:left;padding:10px;border-bottom:1px solid #d9e1e6}.notice{background:#fff3dc;padding:16px;margin:18px 0}pre{font-size:12px;white-space:pre-wrap}small,footer{font-size:12px;color:#536274}</style><main><small>RVT CLEAN-ROOM RESEARCH · NATIVE SOLIDS AND INDEPENDENT IFC MESHES</small><h1>Three new walls in one coordinated save</h1>'''
    body=body.replace('Three new walls in one coordinated save',f'{total_walls} new walls in one coordinated save')
    body+=f'<div class="cards"><div class="card"><strong class="big">{native["prior_native_identities_preserved"]:,}</strong>existing native identities preserved</div><div class="card"><strong class="big">{ifc["existing_wall_meshes_exactly_unchanged"]}</strong>existing wall meshes unchanged</div><div class="card"><strong class="big">{total_walls} walls / 1 episode</strong>distinct IDs and registrations</div></div>'
    body+='<img style="width:100%" src="meshes.svg" alt="Actual IFC meshes at equal scale">'
    if total_walls>3:body+=f'<p>Showing the first three actual meshes of {total_walls} independently checked new walls. All mesh arrays and full validation reports are archived.</p>'
    body+='<table><thead><tr><th>Native ID</th><th>Length</th><th>Saved native solid volume</th><th>Faces / edges / vertices</th></tr></thead><tbody>'+rows+'</tbody></table>'
    body+='<p>Native face loops, closed-solid incidence, volume and saved bounds are measured independently from the actual saved RVT. The plots above use separately triangulated IFC meshes. Source partitions and existing geometry are retained.</p>'
    body+='<div class="notice"><strong>Validation boundary:</strong> local research checks passed. This is not a Revit UI capture. Foreign-producer encoding, native regeneration and Autodesk acceptance remain unverified. IFC schema checks use explicitly recorded OwnerHistory correction controls.</div>'
    body+='<pre>Candidate SHA-256: '+html.escape(candidate)+'</pre><footer>Captured '+timestamp+' · commit '+revision[:12]+'. Input reports, actual mesh arrays, measurements and hashes are archived beside this screenshot.</footer></main></html>'
    page=output/'batch.html';page.write_text(body)
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:raise RuntimeError('Chrome is required')
    with tempfile.TemporaryDirectory(prefix='rvt-batch-browser-') as profile:
        subprocess.run([chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',f'--user-data-dir={profile}','--hide-scrollbars','--window-size=1340,1300',f'--screenshot={output}/batch.png',page.as_uri()],check=True,capture_output=True,timeout=45)
    manifest={'captured_at_utc':timestamp,'source_commit':revision,'working_tree_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
              'browser':subprocess.check_output([chrome,'--version'],text=True).strip(),'matplotlib_version':matplotlib.__version__,'numpy_version':np.__version__,
              'generator_sha256':sha(Path(__file__)),'actual_ifc_meshes':True,'not_autodesk_ui':True,
              'source_report_sha256':{n:hashlib.sha256(r).hexdigest() for n,r in raws.items()},
              'artifacts':{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'destination':str(output),'candidate_sha256':candidate}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_directory',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    print(json.dumps(capture(a.run_directory,a.destination)))
