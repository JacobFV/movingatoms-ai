"""Independently decode hypothetical2024 mesh instance bodies, never a saved RVT."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from directshape_current import construct
from native_mesh import cuboid,audit_closed


def run(schema_path,profile_path,legacy_path,probe,output):
 schema=json.loads(schema_path.with_suffix('.json').read_text());profile=json.loads(profile_path.read_text());legacy=json.loads(legacy_path.read_text())
 root=next(r for r in legacy['records']if r['channel']==102)['representatives']['DirectShape']['fields']
 config={'category_id':-2000011,'style_id':113,'interior_style_id':119,'header_flags':8488,'can_create_parts_status':0,
  'application_id':'82c29ad8-927c-49a8-9c1a-726eae1f745b','application_data_id':'research-cuboid-001','name':'Experimental mesh cuboid',
  'options':{'m_PresentationType':0,'m_ReferencingOption':0,'m_RoomBoundingOption':0,'m_AllowsChangeTypeId':False,'m_AllowsCopy':True,'m_AllowsLock':False,'m_AllowsMove':True,'m_AllowsTagAlongCurve':False}}
 points,triangles=cuboid();bodies,graphs,report=construct(schema,profile,root,133210,points,triangles,config,acknowledge_hypotheses=True)
 output.mkdir(parents=True,exist_ok=False);checks=[];decoded={}
 for channel,body in bodies.items():
  path=output/f'{channel}.bin';path.write_bytes(body)
  graph=json.loads(subprocess.check_output([str(probe),'decode',str(schema_path),str(path)]))['graph'];decoded[channel]=graph
  if graph['consumed_bytes']!=len(body)or [(o['class_name'],o['fields'])for o in graph['objects']]!=[(o['class_name'],o['fields'])for o in graphs[channel]['objects']]:
   # Decoder adds physical pointer offsets; compare semantic pointer fields only.
   def semantic(v):
    if isinstance(v,dict):return {k:semantic(w)for k,w in v.items()if k!='offset'}
    if isinstance(v,(list,tuple)):return [semantic(w)for w in v]
    return v
   if graph['consumed_bytes']!=len(body)or semantic([(o['class_name'],o['fields'])for o in graph['objects']])!=semantic([(o['class_name'],o['fields'])for o in graphs[channel]['objects']]):raise ValueError('independent decode differs')
  checks.append({'channel':channel,'objects':len(graph['objects']),'body_bytes':len(body),'independent_fields_exact':True})
  (output/f'{channel}-decoded.json').write_text(json.dumps(graph,indent=2)+'\n')
 actual=next(o for o in decoded[103]['objects']if o['class_name']=='FacetedTopology0')['fields'];geometry=audit_closed(actual['m_pointsArr'],actual['m_facetsArr'])
 if geometry!=report['mesh']['quantized_geometry']:raise ValueError('decoded geometry differs')
 report.update(independent_decode=checks,decoded_geometry=geometry,schema_sha256=hashlib.sha256(schema_path.read_bytes()).hexdigest(),
  reader_revision=profile['reader_revision'],source_sha256=profile['source_sha256'],projection_scope='Closed topology measured from independently decoded103; no IFC export or saved-document projection')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('schema','profile','legacy','probe','output','result'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();r=run(a.schema,a.profile,a.legacy,a.probe,a.output);a.result.write_text(json.dumps(r,indent=2)+'\n')
