"""Independent full-body decoder and exact public saved-scene triangle checks."""
import hashlib
import json
import math
from pathlib import Path
import subprocess


def semantic(value):
 if isinstance(value,dict):return {k:semantic(v)for k,v in value.items()if k!='offset'}
 if isinstance(value,(list,tuple)):return [semantic(v)for v in value]
 return value


def verify(bodies,graphs,components,schema,decode_probe,scene_probe,output):
 output.mkdir(parents=True,exist_ok=False);checks=[]
 for channel,body in bodies.items():
  path=output/f'{channel}.bin';path.write_bytes(body)
  actual=json.loads(subprocess.check_output([str(decode_probe),'decode',str(schema),str(path)]))['graph']
  expected=[(o['class_name'],o['fields'])for o in graphs[channel]['objects']]
  if actual['consumed_bytes']!=len(body)or semantic([(o['class_name'],o['fields'])for o in actual['objects']])!=semantic(expected):raise ValueError('independent native fields differ')
  (output/f'{channel}-decoded.json').write_text(json.dumps(actual,indent=2)+'\n')
  checks.append({'channel':channel,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'objects':len(actual['objects']),'all_fields_equal':True})
 scene=json.loads(subprocess.check_output([str(scene_probe),str(schema),str(output/'103.bin')]))
 if scene['diagnostics']or len(scene['primitives'])!=len(components):raise ValueError('public saved-scene primitives differ')
 triangles=0;max_normal_error=0.
 for component,primitive in zip(components,scene['primitives'],strict=True):
  fields=component['fields'];expected=[fields['m_pointsArr'][i]for tri in fields['m_facetsArr']for i in tri]
  indices=[[i,i+1,i+2]for i in range(0,len(expected),3)]
  if primitive['vertices']!=expected or primitive['triangles']!=indices:raise ValueError('saved-scene ordered triangle vertices differ')
  normals=[[v/math.sqrt(sum(x*x for x in n))for v in n]for n in fields['m_normalsArr']for _ in range(3)]
  if len(normals)!=len(primitive['normals']):raise ValueError('saved-scene normal count differs')
  error=max(math.dist(a,b)for a,b in zip(normals,primitive['normals'],strict=True));max_normal_error=max(max_normal_error,error)
  if error>1e-14:raise ValueError('saved-scene normals differ')
  triangles+=len(indices)
 return {'independent_decode':checks,'saved_scene':{'primitive_count':len(components),'triangle_count':triangles,'ordered_vertices_and_indices_exact':True,'maximum_normal_error':max_normal_error,'diagnostics':scene['diagnostics']},'decode_probe_sha256':hashlib.sha256(Path(decode_probe).read_bytes()).hexdigest(),'scene_probe_sha256':hashlib.sha256(Path(scene_probe).read_bytes()).hexdigest(),'schema_sha256':hashlib.sha256(Path(schema).read_bytes()).hexdigest(),'autodesk_acceptance':'not_tested'}
