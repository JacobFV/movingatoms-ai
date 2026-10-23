"""Audit measured key offsets and decode independently encoded width variants."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from wall_thickness import encode_wall,thickness_profile,SOURCE_WIDTH
from wall_brep_audit import audit_graph
from new_element_experiment import SOURCE_SHA
from schema_probe import REV


def run(source,probe,schema):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source pin differs')
    profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
    if hashlib.sha256(schema.read_bytes()).hexdigest()!=profile['schema_sha256']:raise ValueError('schema differs')
    def extract(ident):return json.loads(subprocess.check_output([str(probe),str(source),str(ident)]))
    report={'source_sha256':SOURCE_SHA,'reader_revision':REV,'source_types':[],'width_variants':[]}
    widths={}
    for ident in (17328,17337,17341,3897):
        record=next(r for r in extract(ident)['records']if r['channel']==102)
        cs=[o for o in record['graph']['objects']if o['class_name']=='CompoundStructure']
        if len(cs)!=1 or len(cs[0]['fields']['m_layers'])!=1:raise ValueError('requires measured single-layer type')
        width=cs[0]['fields']['m_layers'][0]['m_layerWidth'];widths[ident]=width
        report['source_types'].append({'id':ident,'width_feet':width,'source':record['source']})
    checks=[]
    for record in extract('class:SWall')['records']:
        if record['channel']!=102 or not record.get('graph'):continue
        fields=record['graph']['objects'][0]['fields'];typ=fields['m_WallAttributesId']['m_id']['m_id64']
        if typ not in widths or fields['m_wallKeyRef']!=2 or fields['m_isFlipped']:continue
        if abs(fields['m_keyRefOffset']-widths[typ]/2)>1e-12 or fields['m_locLineOffset']!=0:raise ValueError('key-reference half-width relationship differs')
        checks.append({'id':fields['m_id']['m_id']['m_id64'],'type':typ,'key_offset_feet':fields['m_keyRefOffset'],'body_sha256':record['source']['body_sha256']})
    report['existing_half_width_reference_checks']=checks
    if thickness_profile(profile,SOURCE_WIDTH)[0]!=profile:raise ValueError('nominal width changes source')
    report['nominal_source_graph_exact']=True
    with tempfile.TemporaryDirectory()as tmp:
        for width in (.2/.3048,.5,1.5):
            bodies,graphs,audit=encode_wall(profile,133210,width_feet=width,height_feet=20,length_feet=12,translation_xy=[400,0],context=profile['external_references'],yaw_degrees=45,room_bounding=False,acknowledge_bounding_hypothesis=True,acknowledge_pending_type_remap=True)
            channels={}
            for ch,body in bodies.items():
                path=Path(tmp)/f'{ch}.bin';path.write_bytes(body)
                result=json.loads(subprocess.check_output([str(probe),'decode',str(schema),str(path)]))
                if result['graph']!=graphs[str(ch)]:raise ValueError('independent decode differs')
                channels[str(ch)]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'independent_graph_exact':True}
            report['width_variants'].append({'width_feet':width,'channels':channels,'thickness_audit':audit['thickness'],'native_brep':audit_graph(graphs['103'])})
    report['target_seed_width_feet']=.2/.3048
    report['requires_existing_target_type_validation_before_save']=True
    report['autodesk_acceptance']='not_tested'
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--probe',type=Path,required=True);p.add_argument('--schema',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.source,a.probe,a.schema);a.result.write_text(json.dumps(result,indent=2)+'\n');print('Measured half-width offsets and nine independently decoded channels pass')
