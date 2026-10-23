"""Typed historical Global ElementId references, with exact source-byte binding."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import olefile
from codec import decode
from save_candidate import unpack_global
from directshape_mesh import declarations_for
from wall_element import GraphEncoder


def typed_references(graph,schema):
 classes={c['tag']:c for c in schema};found=[]
 def walk(tag,value,path):
  c=classes[tag]
  if c['name']=='ElementId':
   found.append({'id':value['m_id']['m_id'],'path':path,'class_tag':tag});return
  if c['parent_reference']['tag']:walk(c['parent_reference']['tag'],value,path)
  def field(f,v,p):
   if f['modifier'] in (0x10,0x11,0x12,0x13,0x50,0x51,0x52,0x53):
    sub=dict(f,modifier=f['modifier']&15)
    for i,item in enumerate(v):field(sub,item,f'{p}[{i}]')
   elif f['base']==14 and f['modifier']==0:
    if len(f['references'])!=1:raise ValueError('ambiguous inline class')
    walk(f['references'][0]['tag'],v,p)
   elif f['base']==13 and f['modifier']==0:field(f['nested_descriptor'],v,p)
  for f in c['fields']:
   key=f['name'] if f['name']in value else c['name']+'::'+f['name']
   field(f,value[key],path+'.'+key)
 for i,obj in enumerate(graph['objects']):walk(obj['class_tag'],obj['fields'],f'objects[{i}]({obj["class_name"]}).fields')
 return found


def run(source,schema,probe,local):
 with olefile.OleFileIO(source)as f:
  stored=f.openstream('Global/Latest').read();inflated,_=unpack_global(decode(stored))
 if inflated[-4:]!=bytes(4):raise ValueError('expected four zero trailing bytes')
 body=inflated[:-4];path=local/'directshape-legacy-global.bin';path.write_bytes(body)
 result=json.loads(subprocess.check_output([str(probe),'decode',str(schema),str(path)]));graph=result['graph'];declarations=result['declarations']
 if GraphEncoder(declarations_for(graph,declarations)).graph(graph)!=body:raise ValueError('Global source exact re-encoding differs')
 refs=typed_references(graph,declarations);targets={308799,308800};hits=[h for h in refs if h['id']in targets]
 raw={str(i):[p for p in range(len(body)-3)if body[p:p+4]==struct.pack('<i',i)]for i in targets}
 entries=[]
 for i,o in enumerate(graph['objects']):
  if o['class_name']=='ElementTrackingData':
   for name in ['m_elems','m_symbols']:
    for j,entry in enumerate(o['fields'][name]):
     if entry['m_categoryId']['m_id']['m_id']==-2000151:entries.append({'path':f'objects[{i}].fields.{name}[{j}]','entry':entry})
 return {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'actual_revit_version':2015,'stream':'Global/Latest',
  'stored_sha256':hashlib.sha256(stored).hexdigest(),'inflated_sha256':hashlib.sha256(inflated).hexdigest(),
  'decoded_bytes':len(body),'excluded_trailing_zero_bytes':4,'objects':len(graph['objects']),'source_exact_reencoding':True,
  'reader_revision':'b6086d41b9758fd9b92f42f0a47b8345b9c58056','typed_ElementId_count':len(refs),'targets':sorted(targets),'typed_hits':hits,'raw_int32_hits':raw,
  'category_tracking_entries':entries,'conclusion':'No instance Global tracker membership is established by this fixture when no matching serialized IDs occur. This does not prove no registration is required in2024.'}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['source','schema','probe','local','result']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();a.result.write_text(json.dumps(run(a.source,a.schema,a.probe,a.local),indent=2)+'\n')
