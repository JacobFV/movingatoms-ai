"""Experimental named-level, multipart mesh model builder on the pinned MIT seed.

Level relationships are persisted in our own extensible-storage metadata only;
DirectShape native associated-level remains the measured unset sentinel.
"""
from copy import deepcopy
import hashlib,json,subprocess,tempfile,uuid,zlib
from pathlib import Path
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
from seed_model_request import validate
from seed_save_context import SOURCE_SHA,register_seed
from seed_level import encode_level
from seed_categories import context_for
from native_mesh_surface import encode_surface
from directshape_surface import construct_components,metres_to_feet
from element_properties_probe import build
from element_properties_storage_batch import attach,register_schema_and_owners
from seed_record_candidate import make as save_records
from schema_probe import REV

HERE=Path(__file__).resolve().parent
APPLICATION_ID='b8620789-7098-5242-b12f-70f99c0517e4'

def sha(data):return hashlib.sha256(data).hexdigest()
def read(name):return json.loads((HERE/'results'/name).read_bytes())

def metadata_properties(spec,level):
    return {'application_properties':deepcopy(spec['properties']),'category':spec['category'],
        'level':None if level is None else {'id':level['id'],'name':level['name'],
            'elevation_m':level['elevation_m'],'native_element_id':level['element_id']}}


def make(source,dest,request,*,reader_source=None,target=None,prebuilt_probe=None,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit experimental lifecycle acknowledgment required')
    normalized=validate(request);source=Path(source);dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    if sha(source.read_bytes())!=SOURCE_SHA:raise ValueError('pinned minimal seed required')
    save_context=read('seed_save_context.json');level_profile=read('seed_level-profile.json')
    categories=read('seed_categories.json');mesh_profile=read('directshape-mesh-profile.json')
    legacy=read('directshape_legacy_audit.json');base_config=read('directshape_current.json')['config']
    if save_context['source_sha256']!=SOURCE_SHA or level_profile['source_sha256']!=SOURCE_SHA or level_profile['reader_revision']!=REV:
        raise ValueError('seed profile provenance differs')
    contexts=[context_for(s['category'],categories,interior_policy='projection',allow_generic_fallback=False)for s in normalized['elements']]
    with olefile.OleFileIO(source)as f:
        schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        raw_global=unpack_global(unpage(f.openstream('Global/Latest').read()))[0]
    schema_sha=sha(schema)
    if any(schema_sha!=p[key]for p,key in [(level_profile,'schema_sha256'),(save_context,'schema_sha256'),(categories,'seed_schema_sha256')]):raise ValueError('actual seed schema mismatch')
    legacy_root=next(r for r in legacy['records']if r['channel']==102)['representatives']['DirectShape']['fields']
    records=[];levels=[];next_id=2746
    for spec in normalized['levels']:
        level={'id':spec['id'],'name':spec['name'],'elevation_m':spec['elevation'],'reused_seed':spec['reuse_seed']}
        if spec['reuse_seed']:level['element_id']=1916
        else:
            level['element_id']=next_id;next_id+=1
            channels=encode_level(level_profile,level['element_id'],spec['name'],spec['elevation']/0.3048,acknowledge_lifecycle_hypothesis=True)
            records.append({'element_id':level['element_id'],'channels':channels})
            level['body_sha256']={str(c):sha(b)for c,b in channels.items()}
        levels.append(level)
    bylevel={l['id']:l for l in levels};new_levels=[l['element_id']for l in levels if not l['reused_seed']]
    owner_ids=list(range(next_id,next_id+len(normalized['elements'])))
    # Source-bound level registration and own-schema registration touch disjoint
    # decoded objects. Re-decode after variable-width level edits before ES edits.
    registered_levels,level_changes=(register_seed(raw_global,save_context['registration_evidence'],[],new_levels)if new_levels else(raw_global,[]))
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='seed-model-build-',dir=dest.parent)as temp:
        work=Path(temp)
        if prebuilt_probe is None:
            if reader_source is None or target is None:raise ValueError('reader_source and target required without explicit bundled probe')
            probe=build(Path(reader_source),Path(target),work)
        else:
            if not isinstance(prebuilt_probe,dict)or set(prebuilt_probe)!={'path','sha256','source_sha256','reader_revision'}:
                raise ValueError('explicit bundled probe binding required')
            probe=Path(prebuilt_probe['path'])
            if (prebuilt_probe['reader_revision']!=REV or sha(probe.read_bytes())!=prebuilt_probe['sha256']
                    or sha((HERE/'element_properties_probe.rs').read_bytes())!=prebuilt_probe['source_sha256']):
                raise ValueError('bundled probe source/revision/binary binding differs')
        schema_path=work/'schema.bin';schema_path.write_bytes(schema)
        global_path=work/'global-levels.bin';global_path.write_bytes(registered_levels)
        decoded=json.loads(subprocess.check_output([str(probe),'esglobal',str(schema_path),str(global_path)]))
        declarations=decoded['declarations']
        registered,expected_global,es_changes=register_schema_and_owners(registered_levels,decoded['graph'],declarations,owner_ids)
        global_path.write_bytes(registered)
        final_global=json.loads(subprocess.check_output([str(probe),'esglobal',str(schema_path),str(global_path)]))
        catalog_path=work/'catalog.json';catalog_path.write_text(json.dumps(final_global['catalog']))
        elements=[]
        for ident,spec,category in zip(owner_ids,normalized['elements'],contexts):
            config=deepcopy(base_config)
            config.update({k:category[k]for k in ('category_id','style_id','interior_style_id','material_id')})
            config.update(application_id=APPLICATION_ID,application_data_id=spec['id'],name=spec['name'])
            components=[];part_audits=[]
            for index,part in enumerate(spec['parts']):
                surface=encode_surface(mesh_profile,metres_to_feet(part['vertices']),part['triangles'])
                part_audits.append({'part_index':index,**surface['report']})
                components.extend(surface['components'])
            bodies,_,construction=construct_components(declarations,mesh_profile,legacy_root,ident,components,config,acknowledge_hypotheses=True)
            body_path=work/f'{ident}-102-before.bin';body_path.write_bytes(bodies[102])
            real_graph=json.loads(subprocess.check_output([str(probe),'decode',str(schema_path),str(body_path)]))
            if real_graph['consumed_bytes']!=len(bodies[102]):raise ValueError('incomplete preattachment body decode')
            if real_graph['objects'][0]['fields']['m_assocLevelId']['m_id']['m_id64']!=-1:raise ValueError('unexpected native associated-level policy')
            props=metadata_properties(spec,bylevel.get(spec['level_id']))
            bodies[102],attachment=attach(real_graph,declarations,bodies[102],spec['id'],spec['name'],props,acknowledge_hypotheses=True)
            body_path.write_bytes(bodies[102])
            attached=json.loads(subprocess.check_output([str(probe),'esdecode',str(schema_path),str(body_path),str(catalog_path)]))
            if attached['consumed_bytes']!=len(bodies[102]):raise ValueError('incomplete attached entity decode')
            records.append({'element_id':ident,'channels':bodies})
            elements.append({'id':spec['id'],'name':spec['name'],'element_id':ident,'level_id':spec['level_id'],
                'native_assoc_level_id':-1,'metadata_properties':props,'config':config,'category_context':category,
                'component_count':len(components),'parts_audits':part_audits,'construction':construction,
                'attachment':attachment,'body_sha256':{str(c):sha(b)for c,b in bodies.items()}})
        evidence={'source_sha256':SOURCE_SHA,'source_global_sha256':sha(raw_global),'registered_global_sha256':sha(registered),
            'method':'Measured datum/level category updates followed by independently redecoded own ES schema/cell owner tracking; DirectShape category membership is an explicit historical hypothesis',
            'changes':level_changes+es_changes}
        episode=uuid.uuid5(uuid.UUID(APPLICATION_ID),json.dumps(normalized,sort_keys=True,ensure_ascii=False))
        plan=save_records(source,dest,records,save_context,registered,evidence,episode_guid=str(episode),timestamp=1792627200,acknowledge_hypotheses=True)
        plan.update(request=deepcopy(request),normalized_request=normalized,levels=levels,elements=elements,
            source_sha256=SOURCE_SHA,seed_schema_sha256=schema_sha,reader_revision=REV,
            new_level_ids=new_levels,new_element_ids=owner_ids,expected_new_ids=[r['element_id']for r in records],
            global_level_changes=level_changes,global_es_changes=es_changes,
            registered_global_sha256=sha(registered),own_es_catalog=final_global['catalog'],
            scaffold_policy='Retain seed Level1916 and its views; reuse only requested exact Level 1 at0m.',
            native_level_association_policy='DirectShape m_assocLevelId=-1; requested level relationship stored in own ES only.',
            input_geometry_policy='Absolute world metre coordinates; all explicit parts and oriented triangles retained subject to declared float32 quantization.',
            production_native_export=False,complete_save_transaction=False)
        plan['hypotheses']+=['DirectShape native lifecycle and category support remain unvalidated.',
            'No native associated-level linkage inferred; application relationship is own ES metadata.',
            'DirectShape category registration is not added; historical no-membership evidence is a hypothesis.',
            'Projection style is the explicit interior-style policy; preview not regenerated.']
        (dest/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n')
        return plan


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','dest','request','reader-source','target'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args()
    plan=make(a.source,a.dest,json.loads(a.request.read_bytes()),reader_source=a.reader_source,target=a.target,acknowledge_hypotheses=a.acknowledge_hypotheses)
    print(json.dumps({'plan':str(a.dest/'plan.json'),'new_ids':plan['expected_new_ids']}))
