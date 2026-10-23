"""Measured wall string-container evidence and independently decoded Comments edits."""
import argparse
from collections import Counter
import hashlib,json,subprocess,zlib
from pathlib import Path
import olefile
from codec import decode as unpage
from fetch_fixture import FILES,HOLDOUTS
from element_properties import declarations_for,set_comments,normalized_objects
from element_properties_probe import build
from partition_segments import decode as partition_decode
from partition_objects import validate
from wall_element import GraphEncoder
from schema_probe import REV


def run(source,target,directory):
    binary=build(source,target,directory);reports=[];core=None
    for name,expected in [(n,h)for _,n,h in FILES]+HOLDOUTS:
        path=directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('fixture mismatch')
        raw=json.loads(subprocess.check_output([str(binary),str(path)]))
        (directory/('element-properties-'+path.stem+'.json')).write_text(json.dumps(raw))
        summary=raw['summary']
        if summary['current_records_outside_route'] or summary['unsupported_graph_records']:
            raise ValueError('wall property inventory needs complete current graphs')
        counts=Counter();sets=0
        for row in raw['items']:
            sets+=bool(row['string_sets'])
            for container in row['string_sets']:
                for pair in container['fields']['m_paramSet']:
                    ident=pair['m_paramId']['m_id'];ident=ident['m_id64']if isinstance(ident,dict)else ident
                    counts[ident]+=1
        schemas=summary['extensible_storage_catalog']['schemas']
        reports.append({'file':name,'sha256':expected,'reader_commit':REV,'walls':len(raw['items']),
             'with_string_parameter_set':sets,'string_parameter_counts':dict(sorted(counts.items())),
             'wall_extensible_storage_cells':sum(len(r['es_cells'])for r in raw['items']),
             'owned_es_schemas':[{'guid':guid,'name':s['name'],'fields':[
                 {k:f[k]for k in ('name','type_name','container_type')}for f in s['fields']]}
                 for guid,s in schemas.items()]})
        if name=='core2024.rvt':core=raw
    example=min(core['examples'],key=lambda r:r['source']['body_bytes'])
    with olefile.OleFileIO(directory/'core2024.rvt') as file:
        schema=zlib.decompress(unpage(file.openstream('Formats/Latest').read()),31)
        (directory/'element-properties.schema').write_bytes(schema)
        declarations=json.loads(subprocess.check_output([str(binary),'schema',str(directory/'element-properties.schema')]))
        trials=[]
        for mode,record in [('replace',example),('create',core['null_example'])]:
            graph=record['graph'];ident=record['identity']['element_id']
            partition=partition_decode(unpage(file.openstream(record['source']['stream']).read()))
            actual=next(r.body for r in validate(partition.segments[0],8)[102]if r.element_id==ident)
            decl=declarations_for(declarations,[graph],['ParamValueSetAString']);encoder=GraphEncoder(decl)
            if encoder.graph(graph)!=actual or hashlib.sha256(actual).hexdigest()!=record['source']['body_sha256']:
                raise ValueError('source reconstruction differs')
            body,expected,change=set_comments(graph,decl,'Moving Atoms measured Comments test 😀',
                expected=''if mode=='replace'else None,allow_create=mode=='create')
            out=directory/f'element-properties-{mode}.bin';out.write_bytes(body)
            decoded=json.loads(subprocess.check_output([str(binary),'decode',str(directory/'element-properties.schema'),str(out)]))
            if normalized_objects(decoded)!=expected or encoder.graph(decoded)!=body:
                raise ValueError('independent property graph differs')
            trials.append({'mode':mode,'source_element':ident,'source_bytes':len(actual),
                'source_body_sha256':hashlib.sha256(actual).hexdigest(),'source_reconstruction_exact':True,
                'output_bytes':len(body),'output_body_sha256':hashlib.sha256(body).hexdigest(),
                'independent_full_graph_equal_expected':True,'complete_body_consumed':decoded['consumed_bytes']==len(body),
                'declaration_classes':[{'name':c['name'],'tag':c['tag']}for c in decl if c['name'].startswith('ParamValue')],**change})
    return {'fixtures':reports,'parameter_declarations':[c for c in declarations if c['name']in ('ParamValueSetAString','ParamValueAString')],'trials':trials,'mark_parameter_measured_in_walls':False,
        'arbitrary_metadata_schema_registration_implemented':False,'complete_native_save':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.target,a.directory),indent=2))
