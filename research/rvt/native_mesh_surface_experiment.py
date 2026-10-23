"""Independent public-reader triangle preservation for surface chunks."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
from native_mesh_surface import encode_surface,open_plane,two_components,large_index_surface
from native_mesh_scene_experiment import wrapper
from schema_probe import REV


def run(reader,target,schema,profile_path):
    reader=reader.resolve();target=target.resolve();profile=json.loads(profile_path.read_bytes())
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader pin differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    report={'reader_revision':REV,'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        'scope':'Independent diagnostic saved-graphics primitives; no DirectShape element or document created',
        'decoder_limits':{'values':1000000,'objects':100,'depth':128},'cases':[],'autodesk_acceptance':'not_tested'}
    with tempfile.TemporaryDirectory()as tmp:
        work=Path(tmp);(work/'src').mkdir();(work/'src/main.rs').write_bytes(Path(__file__).with_name('native_mesh_surface_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-native-mesh-surface-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-native-mesh-surface-probe'
        for name,builder in [('open_plane',open_plane),('two_components',two_components),('large_index_chunks',large_index_surface)]:
            points,triangles=builder();encoded=encode_surface(profile,points,triangles);checks=[];emitted=[]
            quantized=[[struct.unpack('<f',struct.pack('<f',v))[0]for v in p]for p in points]
            for component in encoded['components']:
                path=work/'body.bin';path.write_bytes(wrapper(profile,component['fields']))
                decoded=json.loads(subprocess.check_output([str(binary),str(schema),str(path)]))
                actual=[o for o in decoded['graph']['objects']if o['class_name']=='FacetedTopology0']
                if len(actual)!=1 or actual[0]['fields']!=component['fields']:raise ValueError('independent surface fields differ')
                scene=decoded['graphics']
                if scene['diagnostics']or len(scene['primitives'])!=1:raise ValueError('saved-graphics surface rejected')
                primitive=scene['primitives'][0];ids=component['audit']['input_face_indices']
                expected=[quantized[i]for f in ids for i in triangles[f]]
                if primitive['vertices']!=expected or primitive['triangles']!=[[i*3,i*3+1,i*3+2]for i in range(len(ids))]:raise ValueError('rendered triangle geometry/order differs')
                for i,face in enumerate(ids):
                    a,b,c=[quantized[v]for v in triangles[face]];u=[b[j]-a[j]for j in range(3)];v=[c[j]-a[j]for j in range(3)]
                    n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n));n=[x/length for x in n]
                    if any(math.dist(p,n)>1e-7 for p in primitive['normals'][i*3:i*3+3]):raise ValueError('rendered facet normal differs')
                emitted.extend(ids)
                checks.append({k:v for k,v in component['audit'].items()if k not in ('global_vertex_indices','input_face_indices')}|{'independent_fields_exact':True,'rendered_triangles_exact':True,'normals_match_face_winding':True,'input_face_start':ids[0],'input_face_end':ids[-1]})
            if emitted!=list(range(len(triangles))):raise ValueError('rendered face inventory changed')
            summary={k:v for k,v in encoded['report'].items()if k not in ('connected_components','input_to_welded_vertex')}
            summary['vertex_weld_mapping_sha256']=hashlib.sha256(json.dumps(encoded['report']['input_to_welded_vertex']).encode()).hexdigest()
            report['cases'].append({'name':name,'summary':summary,'chunks':checks,'all_input_triangles_rendered_in_order':True})
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('reader','target','schema','profile','result'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=run(a.reader,a.target,a.schema,a.profile);a.result.write_text(json.dumps(result,indent=2)+'\n');print('Open/disconnected/33000-vertex surfaces independently render every triangle exactly')
