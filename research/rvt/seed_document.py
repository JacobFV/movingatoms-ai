"""Bounded named-level/metre-wall document builder on the licensed minimal seed.

Native acceptance and lifecycle semantics remain unproven. No donor streams,
project settings, materials or views are copied into the seed.
"""
from copy import deepcopy
import argparse
import hashlib
import json
import math
from pathlib import Path
import uuid
import zlib
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
import element_table
from seed_save_context import SOURCE_SHA,register_seed
from seed_document_request import validate,FEET_PER_METRE
from seed_document_context import remap
from seed_wall_candidate import DONOR_SHA,TYPE_WIDTH_FEET
from seed_level import encode_level
from wall_element import GraphEncoder
from wall_thickness import encode_wall
from wall_parametric import source_frame
from new_element_experiment import references
from schema_probe import REV

NAMESPACE=uuid.UUID('b8620789-7098-5242-b12f-70f99c0517e4')


def make(source,dest,wall_profile,level_profile,save_context,wall_context,request,*,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit experimental seed/document hypotheses acknowledgment required')
    normalized=validate(request);source=Path(source);dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('requires pinned minimal seed')
    if (wall_profile['source_sha256']!=DONOR_SHA or wall_profile['reader_revision']!=REV
            or level_profile['source_sha256']!=SOURCE_SHA or level_profile['reader_revision']!=REV
            or save_context['source_sha256']!=SOURCE_SHA or wall_context['seed_sha256']!=SOURCE_SHA
            or wall_context['source_sha256']!=DONOR_SHA or wall_context['reader_revision']!=REV):
        raise ValueError('profile provenance mismatch')
    compatible=wall_context['compatible_classes']
    if {c['tag']for c in compatible}!={c['tag']for c in wall_profile['declarations']}or any(not c['identical_descriptor_and_opaque_entries']for c in compatible):
        raise ValueError('required schema classes differ')
    if abs(wall_context['seed_wall_type']['width_feet']-TYPE_WIDTH_FEET)>1e-12:raise ValueError('seed type width differs')
    with olefile.OleFileIO(source)as f:
        schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        table=element_table.decode(unpack_global(unpage(f.openstream('Global/ElemTable').read()))[0],8)
        global_raw=unpack_global(unpage(f.openstream('Global/Latest').read()))[0]
    schema_sha=hashlib.sha256(schema).hexdigest()
    if any(schema_sha!=profile['schema_sha256']for profile in (level_profile,save_context))or schema_sha!=wall_context['seed_schema_sha256']:
        raise ValueError('actual seed schema differs')
    if table.last_id!=2745:raise ValueError('unexpected seed allocator')
    existing={table.current(row)for row in table.rows}
    context={item['source_id']:item['target_id']for item in wall_context['existing_mapping']}
    if context!={3:4,87:91,113:119,119:125,681:796,17328:1947,20308:1916}:raise ValueError('unmeasured seed context map')
    if not(set(context.values())|{1910})<=existing:raise ValueError('required seed definitions missing')
    levels=[];records=[];next_id=table.last_id+1
    for level in normalized['levels']:
        entry={'name':level['name'],'elevation_m':level['elevation'],'reused_seed':level['reuse_seed']}
        if level['reuse_seed']:entry['element_id']=1916
        else:
            entry['element_id']=next_id;next_id+=1
            bodies=encode_level(level_profile,entry['element_id'],entry['name'],entry['elevation_m']*FEET_PER_METRE,
                acknowledge_lifecycle_hypothesis=True)
            records.append({'element_id':entry['element_id'],'channels':bodies})
            entry['body_sha256']={str(c):hashlib.sha256(b).hexdigest()for c,b in bodies.items()}
        levels.append(entry)
    byname={level['name']:level for level in levels}
    anchor,axis,_=source_frame(wall_profile);axis_yaw=math.degrees(math.atan2(axis[1],axis[0]))
    encoder=GraphEncoder(wall_profile['declarations']);walls=[]
    expected_new_ids=list(range(table.last_id+1,table.last_id+1+sum(not level['reused_seed']for level in levels)+len(normalized['walls'])))
    for spec in normalized['walls']:
        ident=next_id;next_id+=1;base=byname[spec['base_level']];top=byname[spec['top_level']]
        mapping=context|{20308:base['element_id'],20307:top['element_id']}
        yaw=(spec['yaw_degrees']-axis_yaw+180)%360-180
        translation=[spec['start'][i]*FEET_PER_METRE-anchor[i]for i in range(2)]
        _,graphs,geometry=encode_wall(wall_profile,ident,width_feet=TYPE_WIDTH_FEET,
            length_feet=spec['length']*FEET_PER_METRE,height_feet=spec['height']*FEET_PER_METRE,
            translation_xy=translation,yaw_degrees=yaw,context=wall_profile['external_references'],
            room_bounding=False,acknowledge_bounding_hypothesis=True,acknowledge_pending_type_remap=True)
        mapped,context_audit=remap(graphs,wall_profile['declarations'],mapping,new_id=ident,
            base_level_id=base['element_id'],base_elevation_feet=base['elevation_m']*FEET_PER_METRE,
            top_elevation_feet=top['elevation_m']*FEET_PER_METRE,type_width_feet=TYPE_WIDTH_FEET)
        positive={ref['id']for graph in mapped.values()for ref in references([o['fields']for o in graph['objects']])if ref['id']>0}
        if not positive<=existing|set(expected_new_ids):raise ValueError('new wall has unresolved references')
        bbox=mapped['103']['objects'][0]['fields']['m_bBox']
        if any(not any(bbox[1][i]<wall['bbox'][0][i]or wall['bbox'][1][i]<bbox[0][i]for i in range(3))for wall in walls):
            raise ValueError('wall bounds touch/intersect; join lifecycle is unsupported')
        bodies={int(c):encoder.graph(graph)for c,graph in mapped.items()}
        records.append({'element_id':ident,'channels':bodies})
        walls.append({'id':spec['id'],'element_id':ident,'request':deepcopy(spec),
            'base_level_id':base['element_id'],'top_level_id':top['element_id'],
            'base_elevation_m':base['elevation_m'],'top_elevation_m':top['elevation_m'],
            'top_offset_m':base['elevation_m']+spec['height']-top['elevation_m'],
            'bbox':bbox,'candidate_id_mapping':mapping,'positive_references':sorted(positive),
            'body_sha256':{str(c):hashlib.sha256(b).hexdigest()for c,b in bodies.items()},
            'geometry_audit':geometry,'context_audit':context_audit})
    new_levels=[level['element_id']for level in levels if not level['reused_seed']]
    new_walls=[wall['element_id']for wall in walls]
    registered,changes=register_seed(global_raw,save_context['registration_evidence'],new_walls,new_levels)
    evidence={'source_sha256':SOURCE_SHA,'source_global_sha256':hashlib.sha256(global_raw).hexdigest(),
        'registered_global_sha256':hashlib.sha256(registered).hexdigest(),
        'method':'measured seed structural wall, datum and level-category registration; no new plan views','changes':changes}
    episode=uuid.uuid5(NAMESPACE,json.dumps(normalized,sort_keys=True,ensure_ascii=False))
    from seed_record_candidate import make as save_records
    plan=save_records(source,dest,records,save_context,registered,evidence,
        episode_guid=str(episode),timestamp=1792627200,acknowledge_hypotheses=True)
    plan.update(request=deepcopy(request),normalized_request=normalized,source_sha256=SOURCE_SHA,donor_sha256=DONOR_SHA,
        reader_revision=REV,seed_schema_sha256=schema_sha,new_episode_guid=str(episode),new_episode=1,new_partition='Partitions/1',
        expected_new_ids=expected_new_ids,new_level_ids=new_levels,new_wall_ids=new_walls,levels=levels,walls=walls,
        scaffold_policy='Retain seed Level1916 and dependent views. Reuse only exact requested Level 1 at0m; other named levels are fresh.',
        world_start_semantics='Wall driver centerline start in world metres; yaw is counterclockwise from +X.',
        wall_type_id=1947,wall_type_width_metres=0.2,complete_save_transaction=False,production_native_export=False,
        hypotheses=plan['hypotheses']+['Unsigned native acceptance remains untested.','Known trackers suffice for new named levels and nonbounding walls.',
            'No new dependent views or preview regeneration.','No wall joins: touching or overlapping bounds are rejected.'])
    (dest/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('dest',type=Path);p.add_argument('--request',type=Path,required=True)
    p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args();results=Path(__file__).parent/'results'
    def read(name):return json.loads((results/name).read_bytes())
    print(json.dumps(make(a.source,a.dest,read('wall-element-profile.json'),read('seed_level-profile.json'),read('seed_save_context.json'),
        read('seed_wall_context.json'),json.loads(a.request.read_bytes()),acknowledge_hypotheses=a.acknowledge_hypotheses),indent=2))
