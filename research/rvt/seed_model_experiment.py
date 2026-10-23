"""Build and verify a named-level/multipart SI mesh research RVT, no-clobber.

Native application acceptance and complete lifecycle semantics remain untested.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from schema_probe import REV
from wall_batch_experiment import code_snapshot,digest,publish_checked,write_json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PROFILE_NAMES=('seed_save_context.json','seed_level-profile.json','seed_categories.json','directshape-mesh-profile.json','directshape_legacy_audit.json','directshape_current.json')


def bind_transport(report,source_sha,candidate_sha):
 if report.get('input_sha256')!=source_sha or report.get('output_sha256')!=candidate_sha:raise ValueError('transport byte binding differs')
 return {**report,'source_sha256':source_sha,'candidate_sha256':candidate_sha}


def validate_bindings(reports,source_sha,candidate_sha):
 if not reports or any(r.get('source_sha256')!=source_sha or r.get('candidate_sha256')!=candidate_sha for r in reports):raise ValueError('all reports must bind source and candidate')


def verify_plan_metadata(plan,metadata):
 if sorted(plan['expected_new_ids'])!=sorted(metadata['table']['new_ids']):raise ValueError('actual allocation differs from model plan')
 for row in [l for l in plan['levels']if not l['reused_seed']]+plan['elements']:
  for channel,value in row['body_sha256'].items():
   if metadata['body_sha256'][str(channel)][str(row['element_id'])]!=value:raise ValueError('saved body hash differs from planned body')


def runtime_snapshot(runtime):
 files=list(HERE.glob('*.py'))+list(HERE.glob('*.rs'))
 probes=[Path(runtime['properties_probe']['path'])]+[Path(runtime['verifier_probes'][key])for key in ('index','scene')]
 return {str(p):digest(p)for p in sorted(files+probes)}


def run(source,output,request_path,reader,target,writer,*,acknowledge_hypotheses=False,runtime=None):
 if not acknowledge_hypotheses:raise ValueError('explicit experimental native lifecycle acknowledgment required')
 from seed_model import make
 from seed_model_request import validate
 from seed_metadata_audit import run as metadata_audit
 from seed_model_verify import verify as native_audit
 from seed_save_context import SOURCE_SHA
 source,output,request_path,writer=(Path(p).resolve()for p in(source,output,request_path,writer))
 reader=Path(reader).resolve()if reader is not None else None
 target=Path(target).resolve()if target is not None else None
 if runtime is not None and (set(runtime)!={'reader_revision','properties_probe','verifier_probes'}or runtime['reader_revision']!=REV):raise ValueError('unsupported standalone runtime binding')
 if output.exists():raise FileExistsError(output)
 if digest(source)!=SOURCE_SHA:raise ValueError('pinned minimal seed required')
 request_bytes=request_path.read_bytes();request=json.loads(request_bytes);validate(request)
 if runtime is None:
  if reader is None or target is None:raise ValueError('reader and target required outside bundled runtime')
  if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('pinned reader revision differs')
  subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
 profiles={name:(HERE/'results'/name).read_bytes()for name in PROFILE_NAMES};snapshot=(lambda:runtime_snapshot(runtime))if runtime is not None else code_snapshot;code=snapshot();writer_sha=digest(writer)
 output.mkdir(parents=True,exist_ok=False);(output/'request.json').write_bytes(request_bytes)
 report={'status':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':SOURCE_SHA,
  'source_commit':None if runtime is not None else subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'reader_revision':REV,'bundled_runtime':runtime is not None,
  'request_sha256':hashlib.sha256(request_bytes).hexdigest(),'code_sha256':code,'writer_sha256':writer_sha,
  'profile_sha256':{n:hashlib.sha256(b).hexdigest()for n,b in profiles.items()},'autodesk_acceptance':'not_tested','production_native_export':False}
 write_json(output/'run.json',report)
 try:
  plan=make(source,output/'patches',request,reader_source=reader,target=target,prebuilt_probe=runtime['properties_probe']if runtime is not None else None,acknowledge_hypotheses=True)
  write_json(output/'plan.json',plan);candidate=output/'candidate.rvt'
  transport_raw=subprocess.check_output([str(writer),'patch',str(source),str(candidate),str(output/'patches/manifest.json')])
  (output/'transport-raw.json').write_bytes(transport_raw);candidate_sha=digest(candidate)
  transport=bind_transport(json.loads(transport_raw),SOURCE_SHA,candidate_sha);write_json(output/'transport.json',transport)
  metadata=metadata_audit(source,candidate,expected_global_change=True);verify_plan_metadata(plan,metadata);write_json(output/'metadata.json',metadata)
  # Independent auditor derives expected geometry/properties from user request,
  # not from the builder's body graphs or plan geometry.
  native=native_audit(reader,target,source,candidate,plan,request,prebuilt_probes=runtime['verifier_probes']if runtime is not None else None)
  write_json(output/'native.json',native)
  validate_bindings([transport,metadata,native],SOURCE_SHA,candidate_sha)
  if snapshot()!=code or digest(source)!=SOURCE_SHA or digest(writer)!=writer_sha or request_path.read_bytes()!=request_bytes or any((HERE/'results'/n).read_bytes()!=b for n,b in profiles.items()):raise ValueError('code/source/request/profile/tool changed during verification')
  if runtime is None:
   subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
   if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader changed during verification')
  published=publish_checked(candidate,output/'verified-candidate.rvt',[transport,metadata,native])
  report.update(status='verified_research_candidate',candidate_sha256=published,
   validation_reports={n:digest(output/n)for n in('transport.json','metadata.json','native.json')},
   native_application_acceptance=False,complete_save_transaction=False,completed_at_utc=datetime.now(timezone.utc).isoformat())
  write_json(output/'run.json',report);return report
 except Exception as exc:
  report.update(status='failed',error=f'{type(exc).__name__}: {exc}',completed_at_utc=datetime.now(timezone.utc).isoformat());write_json(output/'run.json',report);raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in('source','output','request'):p.add_argument(name,type=Path)
 p.add_argument('--reader',type=Path,required=True);p.add_argument('--target',type=Path,default=HERE/'local/seed-model-build')
 p.add_argument('--writer',type=Path,default=ROOT/'processing/rvt-native/target/release/ma-rvt-native');p.add_argument('--acknowledge-hypotheses',action='store_true')
 a=p.parse_args();result=run(a.source,a.output,a.request,a.reader,a.target,a.writer,acknowledge_hypotheses=a.acknowledge_hypotheses)
 print(json.dumps({k:result[k]for k in('status','candidate_sha256')},indent=2))
