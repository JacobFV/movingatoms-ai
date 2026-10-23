"""Reproduce measured height/level evidence and independently decode new wall bodies."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from wall_height import encode_wall,height_profile
from wall_brep_audit import audit_graph
from new_element_experiment import SOURCE_SHA
from schema_probe import REV

URL='https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/fb011c91-be7e-f737-28c7-3f1e1917a0e0.htm'

def run(source,probe,schema):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('fixture hash differs')
    profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
    if hashlib.sha256(schema.read_bytes()).hexdigest()!=profile['schema_sha256']:raise ValueError('schema hash differs')
    def extract(i):return json.loads(subprocess.check_output([str(probe),str(source),str(i)]))
    evidence={'source_sha256':SOURCE_SHA,'reader_revision':REV,'parameter_reference':URL,
        'parameter_mapping':{'-1001109':'WALL_TOP_OFFSET','-1001108':'WALL_BASE_OFFSET','-1001105':'WALL_USER_HEIGHT_PARAM'},
        'cached_scalar_note':'-1001101 has no current public enumeration mapping; measured against saved solid height and level/offset equation.',
        'levels':[],'measured_examples':[],'encoded_heights':[]}
    for ident,expected in [(20307,91),(20308,76)]:
        record=next(r for r in extract(ident)['records'] if r['channel']==102)
        root=record['graph']['objects'][0]
        planes=[o['fields'] for o in record['graph']['objects'] if o['class_name']=='Plane']
        if root['class_name']!='Level' or len(planes)!=2 or any(p['m_origin'][2]!=expected or p['m_xVec'][2]!=0 or p['m_yVec'][2]!=0 for p in planes):raise ValueError('level evidence differs')
        evidence['levels'].append({'id':ident,'name':root['fields']['m_text'],'elevation_feet':expected,'source':record['source'],'identity':record['identity']})
    for ident in [20826,20807,20897]:
        records=extract(ident)['records'];record=next(r for r in records if r['channel']==102)
        root=record['graph']['objects'][0]['fields']
        params=next(o['fields']['m_paramSet'] for o in record['graph']['objects'] if o['class_name']=='ParamValueSetDouble')
        values={v['m_paramId']['m_id']['m_id64']:v['m_value'] for v in params}
        bbox=next(r for r in records if r['channel']==103)['graph']['objects'][0]['fields']['m_bBox']
        height=bbox[1][2]-bbox[0][2]
        if root['m_assocLevelId']['m_id']['m_id64']!=20308 or root['m_upToLevelId']['m_id']['m_id64']!=20307 or abs(height-(15+values[-1001109]-values[-1001108]))>1e-9 or abs(height-values[-1001101])>1e-9:
            raise ValueError('measured level-offset-height relationship differs')
        evidence['measured_examples'].append({'id':ident,'base':20308,'top':20307,'parameters':values,'bbox_feet':bbox,'height_feet':height,'source':record['source']})
    if height_profile(profile,15)[0]!=profile:raise ValueError('nominal height changes source')
    evidence['nominal_source_graph_exact']=True
    with tempfile.TemporaryDirectory() as tmp:
        for height in (8,10,20,25):
            bodies,graphs,audit=encode_wall(profile,133210,height_feet=height,length_feet=12,translation_xy=[400,0],context=profile['external_references'],yaw_degrees=45,room_bounding=False,acknowledge_bounding_hypothesis=True)
            checks={}
            for ch,body in bodies.items():
                path=Path(tmp)/f'{ch}.bin';path.write_bytes(body)
                decoded=json.loads(subprocess.check_output([str(probe),'decode',str(schema),str(path)]))['graph']
                if decoded!=graphs[str(ch)]:raise ValueError('independent body graph differs')
                checks[str(ch)]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'independent_graph_exact':True}
            evidence['encoded_heights'].append({'height_feet':height,'channels':checks,'height_audit':audit['height'],'native_brep':audit_graph(graphs['103'])})
    evidence['autodesk_acceptance']='not_tested'
    return evidence

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--probe',type=Path,required=True);p.add_argument('--schema',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.source,a.probe,a.schema);a.result.write_text(json.dumps(result,indent=2)+'\n');print('Measured level/offset examples and four independently decoded three-channel height variants pass')
