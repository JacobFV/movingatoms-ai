"""Plot actual IFC mesh evidence and capture its local report in a browser."""
import argparse
from datetime import datetime,timezone
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
from capture_evidence import ROOT,sha


def capture(dest, *, parametric=False, native_brep=False):
    dest=dest.resolve();dest.mkdir(parents=True,exist_ok=False)
    names=('wall-geometry-evidence','wall-candidate-outside-verification','wall-candidate-outside-ifc-owner-control')
    if parametric:names=('wall-parametric-candidate-geometry','wall-parametric-candidate-verification','wall-parametric-candidate-ifc-owner-control')
    if native_brep:
        if not parametric:raise ValueError('native BRep evidence belongs to parametric candidate')
        names+=('wall-brep-audit',)
    values={};hashes={}
    for name in names:
        raw=(ROOT/'research/rvt/results'/f'{name}.json').read_bytes()
        hashes[name]=hashlib.sha256(raw).hexdigest();values[name]=json.loads(raw)
        (dest/f'{name}.json').write_bytes(raw)
    evidence=values[names[0]];native=values[names[1]];validation=values[names[2]]
    if parametric:
        validation=dict(validation,source_sha256=validation['source_ifc_sha256'],candidate_sha256=validation['candidate_ifc_sha256'],existing_wall_meshes_exactly_preserved=validation['unchanged_existing_wall_meshes'],translation_metres=[121.92,0,0])
    if evidence['units']!='metres' or evidence['coordinates']!='world':raise ValueError('unsupported mesh coordinates')
    if [m['step_sha256'] for m in evidence['meshes']]!=[validation['source_sha256'],validation['candidate_sha256']]:raise ValueError('mesh and validation inputs differ')
    fig=plt.figure(figsize=(11,4.6),layout='constrained');details=[]
    shared_span=np.max([np.ptp(np.array(m['vertices']),axis=0) for m in evidence['meshes']],axis=0)
    for index,mesh in enumerate(evidence['meshes']):
        verts=np.array(mesh['vertices'],dtype=float);faces=np.array(mesh['triangles'],dtype=int)
        if verts.shape!=(8,3) or faces.shape!=(12,3) or not np.isfinite(verts).all():raise ValueError('unexpected evidence mesh')
        ax=fig.add_subplot(1,2,index+1,projection='3d')
        color='#7c8b9b' if index==0 else '#168c7a'
        ax.add_collection3d(Poly3DCollection(verts[faces],facecolors=color,edgecolors='#26384a',linewidths=.6,alpha=.85))
        low=verts.min(axis=0);high=verts.max(axis=0);span=high-low
        center=(low+high)/2;extent=shared_span+np.array([.4,.5,.2])
        ax.set_xlim(center[0]-extent[0]/2,center[0]+extent[0]/2);ax.set_ylim(center[1]-extent[1]/2,center[1]+extent[1]/2);ax.set_zlim(center[2]-extent[2]/2,center[2]+extent[2]/2)
        ax.set_box_aspect(extent);ax.view_init(elev=18,azim=-65)
        ax.set_yticks([round(float(center[1]),2)])
        ax.set_xlabel('World X (m)',fontsize=9);ax.set_ylabel('Y (m)',fontsize=9);ax.set_zlabel('Z (m)',fontsize=9)
        ax.tick_params(labelsize=8)
        ax.set_title(('Source wall' if index==0 else ('New 12-foot wall' if parametric else 'New translated wall'))+f" · {mesh['native_element_id']}",fontsize=12)
        details.append({'native_id':mesh['native_element_id'],'bounds_min_metres':low.tolist(),'bounds_max_metres':high.tolist(),'dimensions_metres':span.tolist()})
    fig.savefig(dest/'wall-meshes.svg');fig.savefig(dest/'wall-meshes.png',dpi=150);plt.close(fig)
    (dest/'plot-measurements.json').write_text(json.dumps(details,indent=2)+'\n')
    timestamp=datetime.now(timezone.utc).isoformat();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    translation=validation['translation_metres'];dimensions=details[1]['dimensions_metres']
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Native wall projection evidence</title><style>body{background:#edf1f5;color:#172338;font:18px Arial;margin:0}main{background:white;max-width:1100px;margin:30px auto;padding:30px;border-top:7px solid #166c61}h1{font-size:31px}.cards{display:flex;gap:18px}.card{background:#eef7f5;padding:17px;flex:1;font-size:17px}strong.big{font-size:27px;display:block}small,footer{font-size:12px;color:#536274}.warning{padding:16px;background:#fff3dc;margin:18px 0}pre{font-size:13px;overflow-wrap:anywhere;white-space:pre-wrap}</style><main><small>RVT CLEAN-ROOM RESEARCH · INDEPENDENT IFC GEOMETRY EVIDENCE</small><h1>Fresh native wall: independent mesh comparison</h1>'''
    body+=f'<div class="cards"><div class="card"><strong class="big">{validation["existing_wall_meshes_exactly_preserved"]}</strong>existing wall meshes unchanged</div><div class="card"><strong class="big">+{translation[0]:.2f} m</strong>world X displacement</div><div class="card"><strong class="big">8 / 12</strong>vertices / triangles in each wall</div></div>'
    body+='<img alt="Actual triangulated meshes shown at equal scale with world coordinates" style="width:100%" src="wall-meshes.svg">'
    body+=f'<p>Bounding dimensions: {dimensions[0]:.4f} × {dimensions[1]:.4f} × {dimensions[2]:.4f} m. Same material and effective thickness; all prior native identities remain unchanged.</p>'
    body+='<p>IFC owner-history correction is a separate explicit export control. Corrected source and candidate pass schema validation; geometry checks use IfcOpenShell / OpenCASCADE, independently of the native reader.</p>'
    body+='<div class="warning"><strong>Validation boundary:</strong> these are technical plots of actual IFC meshes, not Revit UI. The non-room-bounding toggle and native regeneration behavior remain unproven. Autodesk acceptance has not been tested.</div>'
    body+='<pre>Native candidate SHA-256: '+html.escape(native['candidate_sha256'])+'</pre><footer>Captured '+timestamp+' · commit '+revision[:12]+'. Mesh coordinates, IFC hashes, validation reports and plot measurements are archived beside this screenshot.</footer></main></html>'
    if native_brep:
        brep=values['wall-brep-audit']
        if brep['candidate_sha256']!=native['candidate_sha256']:raise ValueError('native BRep candidate differs')
        solid=[g for g in brep['geometry_components'] if g['closed']]
        if len(solid)!=1:raise ValueError('expected one measured native solid')
        solid=solid[0]
        panel=f'<div class="warning"><strong>Independent saved native BRep:</strong> {solid["faces"]} faces, {solid["edges"]} edges, {solid["vertices"]} vertices; closed solid, Euler characteristic {solid["euler_characteristic"]}; volume {solid["volume_cubic_feet"]:.6f} ft³. Decoded directly from this RVT; no IFC or wall-driver dimensions used for this measurement. Four open auxiliary sheets are reported separately.</div>'
        body=body.replace('<pre>Native candidate',panel+'<pre>Native candidate')
    if parametric:body=body.replace('Fresh native wall: independent mesh comparison','Parametric native wall: 9.5 to 12 feet').replace('Bounding dimensions:','New wall dimensions:')
    page=dest/'wall-comparison.html';page.write_text(body)
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome:raise RuntimeError('Chrome required')
    version=subprocess.check_output([chrome,'--version'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='rvt-wall-evidence-') as profile:
        command=[chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',f'--user-data-dir={profile}','--hide-scrollbars','--window-size=1280,1200',f'--screenshot={dest}/wall-comparison.png',page.as_uri()]
        subprocess.run(command,check=True,capture_output=True,text=True,timeout=45)
    manifest={'captured_at_utc':timestamp,'source_commit':revision,'working_tree_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
      'browser':version,'matplotlib_version':matplotlib.__version__,'numpy_version':np.__version__,'generator_sha256':sha(Path(__file__)),
      'source_report_sha256':hashes,'actual_ifc_meshes':True,'not_autodesk_ui':True,'artifacts':{p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()}}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'destination':str(dest),'source_commit':revision,'matplotlib':matplotlib.__version__}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--parametric',action='store_true');p.add_argument('--native-brep',action='store_true')
    a=p.parse_args();print(json.dumps(capture(a.destination,parametric=a.parametric,native_brep=a.native_brep)))
