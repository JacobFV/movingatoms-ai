"""Guarded minimal-seed wall transaction; native application acceptance untested.

Uses measured core wall geometry as a schema profile, never donor streams. Every
external reference is remapped to measured seed definitions or a fresh upper Level.
"""
import argparse
import hashlib
import json
from pathlib import Path
import uuid
import zlib
import olefile
from codec import decode as unpage
import element_table,save_history,save_increments,basic_file_info_codec
from save_candidate import unpack_global,repack_global,advance_regular_ancillary_revisions
from new_element import allocate_identity
from wall_batch_candidate import validate_specs,DEMO_SPECS
from wall_element import GraphEncoder
from partition_builder import build_partition
from partition_objects import Record
from partition_segments import encode as partition_encode
from seed_save_context import SOURCE_SHA,allocation_plan
from schema_probe import REV

DONOR_SHA='c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'
EPISODE_NAMESPACE=uuid.UUID('04f3b8c9-eddd-51f7-a7cd-9e47648688e1')
TYPE_WIDTH_FEET=0.6561679790026247
BASE_LEVEL_ID=1916


def checked_specs(specs):
    result=validate_specs(specs)
    if len(result)>99:raise ValueError('at most99 walls plus one new Level are supported')
    return result


def make(source,dest,wall_profile,level_profile,save_context,wall_context,specs,*,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit unsigned/seed/lifecycle hypotheses acknowledgment required')
    specs=checked_specs(specs);source=Path(source);dest=Path(dest)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('requires pinned MIT minimal2024seed')
    if wall_profile['source_sha256']!=DONOR_SHA or wall_profile['reader_revision']!=REV:
        raise ValueError('donor wall profile provenance differs')
    if level_profile['source_sha256']!=SOURCE_SHA or level_profile['reader_revision']!=REV:
        raise ValueError('seed Level profile provenance differs')
    if save_context['source_sha256']!=SOURCE_SHA:raise ValueError('seed save context provenance differs')
    if (wall_context['source_sha256']!=DONOR_SHA or wall_context['seed_sha256']!=SOURCE_SHA
            or wall_context['reader_revision']!=REV):raise ValueError('reference mapping provenance differs')
    compatible=wall_context['compatible_classes']
    if ({c['tag']for c in compatible}!={c['tag']for c in wall_profile['declarations']}
            or any(not c['identical_descriptor_and_opaque_entries']for c in compatible)):
        raise ValueError('donor classes lack exact seed schema compatibility')
    if abs(wall_context['seed_wall_type']['width_feet']-TYPE_WIDTH_FEET)>1e-12:
        raise ValueError('seed wall type width differs')
    names=['Global/History','Global/ElemTable','Global/DocumentIncrementTable','Contents','BasicFileInfo','Global/Latest','ProjectInformation']
    with olefile.OleFileIO(source)as file:
        stored={n:file.openstream(n).read()for n in names}
        schema=zlib.decompress(unpage(file.openstream('Formats/Latest').read()),31)
        if file.exists('Partitions/1'):raise ValueError('new partition already exists')
    schema_sha=hashlib.sha256(schema).hexdigest()
    if schema_sha!=save_context['schema_sha256'] or schema_sha!=level_profile['schema_sha256'] or schema_sha!=wall_context['seed_schema_sha256']:
        raise ValueError('actual seed schema differs from independent evidence')
    logical={n:unpage(stored[n])for n in names if n not in ('BasicFileInfo','ProjectInformation')}
    history=save_history.decode(unpack_global(logical['Global/History'])[0])
    table=element_table.decode(unpack_global(logical['Global/ElemTable'])[0],8)
    tag,fields=save_increments.decode(unpack_global(logical['Global/DocumentIncrementTable'])[0])
    if history.next_sequence!=1 or table.last_id!=2745 or len(fields['m_increments'])!=1:
        raise ValueError('unexpected seed allocation state')
    episode=uuid.uuid5(EPISODE_NAMESPACE,json.dumps(specs,sort_keys=True))
    allocation=allocation_plan(table,history,fields,len(specs)+1,1792627200,str(episode))
    if allocation['partition_ordinal_hypothesis']!=1:raise ValueError('unexpected partition allocation')
    level_id=allocation['allocated'][0];wall_ids=allocation['allocated'][1:]
    mapping={3:4,87:91,113:119,119:125,681:796,17328:1947,20307:level_id,20308:BASE_LEVEL_ID}
    proven_mapping={entry['source_id']:entry['target_id']for entry in wall_context['existing_mapping']}
    if proven_mapping!={key:value for key,value in mapping.items()if key!=20307}:
        raise ValueError('candidate reference map differs from measured seed context')
    existing_ids={table.current(row)for row in table.rows}
    if not (set(proven_mapping.values())|{1910})<=existing_ids:
        raise ValueError('mapped seed context or Level type is absent from live table')
    from seed_wall_context import remap_graphs
    from wall_thickness import encode_wall
    from seed_level import encode_level
    level_name='Upper level';level_elevation=15.0
    level_bodies=encode_level(level_profile,level_id,level_name,level_elevation,acknowledge_lifecycle_hypothesis=True)
    encoder=GraphEncoder(wall_profile['declarations']);walls=[]
    for ident,spec in zip(wall_ids,specs):
        _,graphs,geometry=encode_wall(wall_profile,ident,width_feet=TYPE_WIDTH_FEET,height_feet=spec.get('height_feet',15),
            length_feet=spec['length_feet'],translation_xy=spec['translation_xy'],yaw_degrees=spec.get('yaw_degrees',0),
            context=wall_profile['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True,
            acknowledge_pending_type_remap=True)
        mapped,remap=remap_graphs(graphs,wall_profile['declarations'],mapping,new_id=ident,
            base_elevation_feet=0,top_elevation_feet=level_elevation,type_width_feet=TYPE_WIDTH_FEET)
        from new_element_experiment import references
        positive_refs={ref['id']for graph in mapped.values()for ref in references([o['fields']for o in graph['objects']])if ref['id']>0}
        if not positive_refs<=(existing_ids|set(allocation['allocated'])):
            raise ValueError('new wall has unresolved positive references')
        bodies={int(ch):encoder.graph(graph)for ch,graph in mapped.items()}
        bbox=mapped['103']['objects'][0]['fields']['m_bBox']
        if any(not any(bbox[1][i]<wall['bbox'][0][i] or wall['bbox'][1][i]<bbox[0][i]for i in range(3))for wall in walls):
            raise ValueError('new wall bounds intersect or touch')
        walls.append({'id':ident,'spec':spec,'bbox':bbox,'bodies':bodies,'geometry_audit':geometry,'reference_remap':remap,'positive_references':sorted(positive_refs)})
    newtable=table
    for expected in allocation['allocated']:
        ident,newtable=allocate_identity(newtable,history)
        if ident!=expected:raise ValueError('allocation helper disagrees')
    newhistory=save_history.prepend_episode(history,episode.bytes_le)
    revised=allocation['increment_fields']
    for name in ('m_increments','m_localIncrements'):
        revised[name][-1]['m_basicFileInfoStreamRevision']+=1
        revised[name][-1]['m_comment']='Unsigned minimal-seed upper-Level and nonbounding walls; lifecycle hypotheses'
    revised=advance_regular_ancillary_revisions(fields,revised)
    revisions={n:revised['m_increments'][-1][f'm_{n}StreamRevision']for n in save_increments.REVISIONS}
    from seed_save_context import register_seed,patch_seed_timestamp,patch_seed_contents
    registered,registration=register_seed(unpack_global(logical['Global/Latest'])[0],save_context['registration_evidence'],wall_ids,[level_id])
    project,timestamp=patch_seed_timestamp(stored['ProjectInformation'],fields['m_increments'][-1]['m_atimeStamp']['m_lsb'],1792627200)
    all_bodies=[(level_id,level_bodies)]+[(wall['id'],wall['bodies'])for wall in walls]
    partition=partition_encode(build_partition(0x37b,{ch:tuple(Record(ident,b[ch])for ident,b in all_bodies)for ch in (101,102,103)},8,allow_unsigned_nonempty=True))
    payloads={
        'Global/History':repack_global(logical['Global/History'],save_history.encode(newhistory)),
        'Global/ElemTable':repack_global(logical['Global/ElemTable'],element_table.encode(newtable)),
        'Global/DocumentIncrementTable':repack_global(logical['Global/DocumentIncrementTable'],save_increments.encode(tag,revised)),
        'Contents':patch_seed_contents(logical['Contents'],save_context,revisions),
        'BasicFileInfo':basic_file_info_codec.encode(basic_file_info_codec.decode(stored['BasicFileInfo']),allocation['new_major_version'],str(episode)),
        'Global/Latest':repack_global(logical['Global/Latest'],registered),'ProjectInformation':project}
    plan={'source_sha256':SOURCE_SHA,'donor_sha256':DONOR_SHA,'reader_revision':REV,'seed_schema_sha256':schema_sha,
        'new_level_id':level_id,'new_level_name':level_name,'new_level_elevation_feet':level_elevation,
        'base_level_id':BASE_LEVEL_ID,'base_level_elevation_feet':0,'new_wall_ids':wall_ids,
        'new_partition':'Partitions/1','new_episode':1,'new_episode_guid':str(episode),'expected_new_ids':allocation['allocated'],
        'candidate_id_mapping':mapping,'wall_type_id':1947,'wall_type_width_feet':TYPE_WIDTH_FEET,
        'source_rows':len(table.rows),'new_rows':len(newtable.rows),'prior_table_rows_byte_identical':newtable.rows[:-len(all_bodies)]==table.rows,
        'level_body_sha256':{str(ch):hashlib.sha256(body).hexdigest()for ch,body in level_bodies.items()},
        'walls':[{k:v for k,v in wall.items()if k!='bodies'}|{'body_sha256':{str(ch):hashlib.sha256(body).hexdigest()for ch,body in wall['bodies'].items()}}for wall in walls],
        'registration_change':registration,'project_information_timestamp':timestamp,
        'partition_payload_sha256':hashlib.sha256(partition).hexdigest(),
        'autodesk_acceptance':'not_tested','complete_save_transaction':False,'production_native_export':False,
        'hypotheses':['Unsigned new partition acceptance.','First-wall structural and new-Level registration suffice.',
            'No new Level plan view required; existing seed view is not copied.','Non-room-bounding walls avoid unavailable room topology regeneration.',
            'Measured seed mappings and equal schema classes suffice across donor/seed.','Preview remains unchanged; native regeneration is unverified.']}
    dest.mkdir(parents=True,exist_ok=False);patches=[]
    for stream,payload in payloads.items():
        name=stream.replace('/','-')+'.bin';(dest/name).write_bytes(payload)
        patches.append({'stream':stream,'expected_stored_sha256':hashlib.sha256(stored[stream]).hexdigest(),'new_payload_file':name})
    (dest/'partition.bin').write_bytes(partition)
    (dest/'manifest.json').write_text(json.dumps({'input_sha256':SOURCE_SHA,'patches':patches,'creates':[{'stream':'Partitions/1','expected_absent':True,'new_payload_file':'partition.bin'}]},indent=2)+'\n')
    (dest/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('dest',type=Path)
    p.add_argument('--specs',type=Path);p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args()
    results=Path(__file__).parent/'results'
    def read(name):return json.loads((results/name).read_bytes())
    print(json.dumps(make(a.source,a.dest,read('wall-element-profile.json'),read('seed_level-profile.json'),
        read('seed_save_context.json'),read('seed_wall_context.json'),json.loads(a.specs.read_bytes())if a.specs else DEMO_SPECS,
        acknowledge_hypotheses=a.acknowledge_hypotheses),indent=2))
