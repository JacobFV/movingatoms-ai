"""SI input→multiple native mesh bodies→independent decoded saved graphics."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from directshape_surface import construct_metres
from directshape_surface_verify import verify
from schema_probe import REV


def run(reader,target,schema,profile_path,legacy_path,config_path,output):
 reader=reader.resolve();target=target.resolve()
 if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
 subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
 output.mkdir(parents=True,exist_ok=False);build=output/'build';(build/'src').mkdir(parents=True)
 (build/'src/main.rs').write_bytes(Path(__file__).with_name('directshape_surface_probe.rs').read_bytes())
 (build/'Cargo.toml').write_text('[package]\nname="rvt-directshape-surface-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
 subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(build/'Cargo.toml'),'--target-dir',str(target)],check=True)
 probe=target/'release/rvt-directshape-surface-probe'
 profile=json.loads(profile_path.read_text());legacy=json.loads(legacy_path.read_text());config=json.loads(config_path.read_text())['config']
 root=next(r for r in legacy['records']if r['channel']==102)['representatives']['DirectShape']['fields']
 declarations=json.loads(schema.with_suffix('.json').read_text());rows=[]
 cases=[('disconnected_open_surface',[[0,0,0],[1,0,0],[0,1,0],[3,0,1],[4,0,1],[3,1,1]],[[0,1,2],[3,4,5]],3),
 ('large_split_surface',[[j*2+dx,dy,0]for j in range(11000)for dx,dy in ((0,0),(1,0),(0,1))],[[3*j,3*j+1,3*j+2]for j in range(11000)],32768)]
 for index,(name,points,triangles,limit)in enumerate(cases):
  bodies,graphs,report,components=construct_metres(declarations,profile,root,133210+index,points,triangles,config,chunk_vertex_limit=limit,acknowledge_hypotheses=True)
  evidence=verify(bodies,graphs,components,schema,probe,probe,output/name)
  # Keep the large exact input in ignored run artifact; durable report binds it.
  inputs={'points_metres':report.pop('input_points_metres'),'triangles':report.pop('input_triangles')}
  raw=json.dumps(inputs,separators=(',',':')).encode();(output/name/'input.json').write_bytes(raw)
  report.update(input_sha256=hashlib.sha256(raw).hexdigest(),input_point_count=len(points),input_triangle_count=len(triangles))
  full={'name':name,**report,'verification':evidence}
  encoded=json.dumps(full,indent=2).encode();(output/name/'audit-full.json').write_bytes(encoded)
  def compact(value):
   if isinstance(value,dict):return {k:compact(v)for k,v in value.items()}
   if isinstance(value,list):
    if len(value)>32:return {'count':len(value),'sha256':hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest(),'first_three':compact(value[:3]),'full_values_in_local_audit':True}
    return [compact(v)for v in value]
   return value
  rows.append({**compact(full),'full_local_audit_sha256':hashlib.sha256(encoded).hexdigest()})
 return {'reader_revision':REV,'source_sha256':profile['source_sha256'],'variants':rows,'document_created':False,'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['reader','target','schema','profile','legacy','config','output','result']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();r=run(a.reader,a.target,a.schema,a.profile,a.legacy,a.config,a.output);a.result.write_text(json.dumps(r,indent=2)+'\n')
