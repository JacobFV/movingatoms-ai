"""Round-trip standalone measured/new mesh components through the public decoder."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from native_mesh import source_component,encode_component,tetrahedron,cuboid,l_prism,torus,audit_closed
from schema_probe import REV


def run(profile_path,schema,probe):
    profile=json.loads(profile_path.read_bytes())
    if profile['reader_revision']!=REV:raise ValueError('profile revision differs')
    evidence={'profile_file':profile_path.name,'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        'source_sha256':profile['source_sha256'],'reader_revision':REV,'schema_sha256':hashlib.sha256(schema.read_bytes()).hexdigest(),
        'probe_binary_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'measured_components':[],'new_components':[],
        'scope':'Standalone FacetedTopology0 component encoding; no GPolyMesh wrapper, element, DirectShape or document created.'}
    with tempfile.TemporaryDirectory()as tmp:
        def verify(body,fields):
            path=Path(tmp)/'body.bin';path.write_bytes(body)
            decoded=json.loads(subprocess.check_output([str(probe),'decode',str(schema),str(path)]))['graph']
            if len(decoded['objects'])!=1 or decoded['objects'][0]['class_name']!='FacetedTopology0' or decoded['objects'][0]['fields']!=fields or decoded['consumed_bytes']!=len(body):
                raise ValueError('independent component decode differs')
            return {'objects':1,'consumed_bytes':decoded['consumed_bytes'],'body_sha256':hashlib.sha256(body).hexdigest(),'independent_fields_exact':True}
        for index in (0,1):
            body,fields,audit=source_component(profile,index)
            evidence['measured_components'].append({'component_index':index,**audit,'independent_decode':verify(body,fields)})
        for name,builder,nonconvex in [('tetrahedron',tetrahedron,False),('cuboid',cuboid,False),('L_prism',l_prism,True),('torus',torus,True)]:
            points,triangles=builder();body,fields,audit=encode_component(profile,points,triangles,allow_nonconvex=nonconvex)
            decoded=verify(body,fields)
            # Re-audit the float32 values independently returned by the decoder.
            path=Path(tmp)/'body.bin'
            actual=json.loads(subprocess.check_output([str(probe),'decode',str(schema),str(path)]))['graph']['objects'][0]['fields']
            measured=audit_closed(actual['m_pointsArr'],actual['m_facetsArr'],allow_nonconvex=nonconvex)
            if measured!=audit['quantized_geometry']:raise ValueError('decoded closed-solid measurements differ')
            evidence['new_components'].append({'name':name,'input_points':points,'input_triangles':triangles,**audit,'independent_decode':decoded})
    return evidence

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,default=Path(__file__).parent/'results/directshape-mesh-profile.json');p.add_argument('--schema',type=Path,required=True);p.add_argument('--probe',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.profile,a.schema,a.probe);a.result.write_text(json.dumps(result,indent=2)+'\n');print('Two measured and four new closed components independently decode exactly')
