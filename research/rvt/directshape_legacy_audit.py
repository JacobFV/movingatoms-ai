"""Report measured historical DirectShape bodies; never asserts current routing."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from directshape_mesh import declarations_for
from wall_element import GraphEncoder


def report(records, old_schema, current_schema):
    old={c['name']:c for c in old_schema}; new={c['name']:c for c in current_schema}
    result={k:records[k] for k in ('historical_only','id_width_bytes','physical_record_count','statistics')}
    result['records']=[]
    for record in records['records']:
        graph=record['graph']; body=bytes.fromhex(record['body_hex'])
        declarations=declarations_for(graph,old_schema)
        encoded=GraphEncoder(declarations).graph(graph)
        if encoded!=body:raise ValueError('historical source-exact encoding differs')
        representatives={}
        for obj in graph['objects']:
            if obj['class_name'] in ['DirectShape','DirectShapeCell','DirectShapeDataCell','GElement','ElementParents']:
                representatives.setdefault(obj['class_name'],obj)
        result['records'].append({k:v for k,v in record.items() if k not in ('graph','body_hex')} | {
            'body_sha256':hashlib.sha256(body).hexdigest(),'source_exact_reencoding':True,
            'consumed_bytes':graph['consumed_bytes'],'objects':len(graph['objects']),
            'class_counts':dict(Counter(o['class_name'] for o in graph['objects'])),
            'representatives':representatives})
    comparisons=[]
    for name in ['DirectShape','DirectShapeCell','DirectShapeDataCell','DirectShapeOptions','GElement','Element','ElementId','FacetedTopology0']:
        a=old.get(name);b=new.get(name)
        comparisons.append({'class':name,'2015':a,'2024':b,
          'added_2024_field_names': sorted({f['name'] for f in b['fields']} - {f['name'] for f in a['fields']}) if a and b else None})
    result['schema_comparison']=comparisons
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['records','old_schema','current_schema','result']:p.add_argument(name,type=Path)
    a=p.parse_args();r=report(*[json.loads(v.read_text()) for v in [a.records,a.old_schema,a.current_schema]])
    source=Path(__file__).parent/'local/directshape-fixtures/singleDirectShape.rvt'
    r.update(source_file=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
      actual_revit_version=2015,reader_revision='b6086d41b9758fd9b92f42f0a47b8345b9c58056',
      source_repository='https://github.com/DynamoDS/DynamoRevit',source_commit='49cd43c5c3b21271640ae043b8b77374e4796843',license='Apache-2.0',
      legacy_declared_body_equation='sum(body_bytes + 4) == declared_body_bytes',
      current_identity_routing_validated=False,native_application_acceptance=False)
    a.result.write_text(json.dumps(r,indent=2)+'\n')
