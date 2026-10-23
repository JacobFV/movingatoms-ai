"""Exercise public saved-graphics normal cardinality using a diagnostic wrapper."""
from copy import deepcopy
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
from wall_element import GraphEncoder
from native_mesh import encode_component,cuboid,l_prism,torus
from schema_probe import REV


def wrapper(profile,fields):
    record=next(r for r in profile['records']if r['channel']==103)
    objects=record['graph']['objects'];root=deepcopy(objects[0]);mesh=deepcopy(next(o for o in objects if o['class_name']=='GPolyMesh'))
    root['fields']['m_subNodes']=[{'class_tag':2142,'pointer_token':3}]
    bounds=[[min(p[i]for p in fields['m_pointsArr'])for i in range(3)],[max(p[i]for p in fields['m_pointsArr'])for i in range(3)]]
    root['fields']['m_bBox']=bounds;root['fields']['m_tightbBox']=bounds
    mesh['fields']['m_pFacetedTopology']={'class_tag':1732,'pointer_token':0xffffffff}
    graph={'objects':[root,mesh,{'class_name':'FacetedTopology0','class_tag':1732,'fields':fields}]}
    return GraphEncoder(record['declarations']).graph(graph)


def run(reader,target,schema,profile_path):
    reader=reader.resolve();target=target.resolve();profile=json.loads(profile_path.read_bytes())
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory()as tmp:
        work=Path(tmp);(work/'src').mkdir();(work/'src/main.rs').write_bytes(Path(__file__).with_name('native_mesh_scene_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-native-mesh-scene-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-native-mesh-scene-probe';rows=[]
        def scene(fields):
            path=work/'wrapper.bin';path.write_bytes(wrapper(profile,fields))
            return json.loads(subprocess.check_output([str(binary),str(schema),str(path)]))
        for name,builder,nonconvex in [('cuboid',cuboid,False),('L_prism',l_prism,True),('torus',torus,True)]:
            _,fields,report=encode_component(profile,*builder(),allow_nonconvex=nonconvex)
            result=scene(fields)
            if result['diagnostics'] or len(result['primitives'])!=1:raise ValueError('saved graphics rejected generated component')
            primitive=result['primitives'][0]
            if len(primitive['triangles'])!=len(fields['m_facetsArr'])or len(primitive['vertices'])!=len(fields['m_facetsArr'])*3:raise ValueError('saved graphics triangle expansion differs')
            expected_vertices=[fields['m_pointsArr'][index]for tri in fields['m_facetsArr']for index in tri]
            expected_normals=[[v/math.sqrt(sum(x*x for x in normal))for v in normal] for normal in fields['m_normalsArr']for _ in range(3)]
            if primitive['vertices']!=expected_vertices or len(primitive['normals'])!=len(expected_normals)or any(math.dist(a,b)>1e-14 for a,b in zip(primitive['normals'],expected_normals)):raise ValueError('saved graphics vertex/normal values differ')
            rows.append({'name':name,'geometry':report,'scene_triangles':len(primitive['triangles']),'scene_vertices':len(primitive['vertices']),'scene_diagnostics':result['diagnostics'],'expanded_vertices_exact_and_unit_normals_match':True})
        _,fields,_=encode_component(profile,*cuboid())
        bad=deepcopy(fields);bad['m_normalsArr']=bad['m_normalsArr'][:8]
        rejection=scene(bad)
        if rejection['primitives']or not any('normal cardinality'in d for d in rejection['diagnostics']):raise ValueError('8 normals/12 facets negative control was not rejected')
        empty=deepcopy(fields);empty['m_normalsArr']=[];flat=scene(empty)
        if flat['diagnostics']or len(flat['primitives'])!=1:raise ValueError('empty normal fallback rejected')
        return {'reader_revision':REV,'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            'scope':'Diagnostic three-object saved-graphics wrapper only; no element/document or DirectShape created',
            'normal_contract':'normalsFlag0 with empty normals or exactly one normal per triangle in pinned public saved-graphics reader',
            'variants':rows,'negative_8_normals_12_triangles':rejection,'empty_normals_flat_fallback_accepted':True,'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reader','target','schema','profile','result'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();result=run(a.reader,a.target,a.schema,a.profile);a.result.write_text(json.dumps(result,indent=2)+'\n');print('Saved graphics accepts cuboid/L-prism/torus; rejects8-normal12-facet control')
