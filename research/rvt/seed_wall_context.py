"""Guarded Core-wall to minimal-2024-seed context mapping, without file mutation."""
from copy import deepcopy
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zlib
import olefile
from codec import decode as unpage
from schema_probe import REV
from wall_element import GraphEncoder
from wall_oriented import solid_vertices
from wall_parametric import edge_consistency

SEED_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'
SOURCE_SHA='c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'
EXTERNAL_IDS={3,87,113,119,681,17328,20307,20308}
EXISTING_MAPPING={3:4,87:91,113:119,119:125,681:796,17328:1947,20308:1916}


def compare_schemas(source,seed):
    """Require equal complete declaration semantics for the source's class closure."""
    sm={c['tag']:c for c in source};tm={c['tag']:c for c in seed}
    names={c['name']:c for c in seed}
    def descriptor(f,classes):
        return {k:f[k]for k in ('name','base','modifier','array_count','raw_descriptor','uninterpreted_flags')}|{
            'references':[classes[r['tag']]['name']for r in f['references']],
            'nested':descriptor(f['nested_descriptor'],classes)if f['nested_descriptor'] else None}
    def signature(c,classes):
        return {'parent':classes[c['parent_reference']['tag']]['name']if c['parent_reference']['tag']else None,
                'version':c['version_like_word'],'fields':[descriptor(f,classes)for f in c['fields']],
                'opaque_count':c['opaque_16byte_entry_count'],'opaque_sha256':c['opaque_entries_sha256']}
    result=[]
    for c in source:
        d=names.get(c['name'])
        if d is None or d['tag']!=c['tag'] or signature(c,sm)!=signature(d,tm):
            raise ValueError('incompatible embedded class '+c['name'])
        result.append({'class_name':c['name'],'tag':c['tag'],'identical_descriptor_and_opaque_entries':True})
    return result


def remap_graphs(graphs,declarations,mapping,*,new_id,base_elevation_feet=0.0,top_elevation_feet=15.0,type_width_feet):
    """Remap explicit ElementIds, relocate world Z, and synchronize top offset.

    Apply after the Core-profile geometric encoder. Caller supplies measured
    destination type width and allocated top level; neither is guessed here.
    """
    mapping={int(k):v for k,v in mapping.items()}
    if set(mapping)!=EXTERNAL_IDS or any(type(v)is not int or v<=0 for v in mapping.values()):
        raise ValueError('complete positive external context mapping required')
    if any(mapping[k]!=v for k,v in EXISTING_MAPPING.items()):raise ValueError('existing seed context mapping differs from measured identities')
    if type(new_id)is not int or new_id<=0 or new_id in mapping.values() or new_id in EXTERNAL_IDS or new_id==20826:
        raise ValueError('fresh distinct wall identity required')
    if mapping[20307]==mapping[20308]:raise ValueError('base and upper level must be distinct')
    if any(type(v)not in (int,float)or not math.isfinite(v)for v in (base_elevation_feet,top_elevation_feet,type_width_feet)) or top_elevation_feet<=base_elevation_feet or type_width_feet<=0:
        raise ValueError('finite ordered levels and positive type width required')
    if set(graphs)!={'101','102','103'}:raise ValueError('three wall channels required')
    result=deepcopy(graphs);encoder=GraphEncoder(declarations);changes=[];found=set()
    def walk(tag,value,path):
        c=encoder.classes[tag]
        if c['name']=='ElementId':
            ident=value['m_id']['m_id64']
            if ident>0:
                if ident==new_id:return
                if ident not in mapping:raise ValueError('unmapped positive ElementId '+str(ident))
                found.add(ident);value['m_id']['m_id64']=mapping[ident]
                changes.append({'path':path,'before':ident,'after':mapping[ident]})
            return
        for name,decl,f in encoder.layouts[tag]:
            if f['base']!=14 or (f['modifier']&15)in (1,2,3) or len(f['references'])!=1:continue
            child=f['references'][0]['tag'];v=value[name]
            def descend(v,p):
                if isinstance(v,list):
                    for i,x in enumerate(v):descend(x,f'{p}[{i}]')
                elif isinstance(v,dict):walk(child,v,p)
            descend(v,path+'.'+name)
    for channel,graph in result.items():
        for i,obj in enumerate(graph['objects']):
            if encoder.classes[obj['class_tag']]['name']!=obj['class_name']:raise ValueError('object class identity mismatch')
            walk(obj['class_tag'],obj['fields'],f'{channel}.objects[{i}]({obj["class_name"]})')
    if found!=EXTERNAL_IDS:raise ValueError('measured external-reference inventory differs')
    root=result['103']['objects'][0]
    if root['class_name']!='GElement' or root['fields']['m_elementId']!=new_id or root['fields']['m_GInfo']['m_tag']!=new_id:
        raise ValueError('geometry owner identity mismatch')
    vertices=solid_vertices(result['103'])
    lines=[o for g in result.values()for o in g['objects']if o['class_name']=='GLine']
    if len(lines)!=1:raise ValueError('one wall driver line required')
    direction=lines[0]['fields']['m_dirVec']
    if len(direction)!=3 or abs(direction[2])>1e-10 or abs(math.hypot(*direction[:2])-1)>1e-10:
        raise ValueError('horizontal unit driver required')
    normal=[-direction[1],direction[0],0.0]
    projections=[sum(v*n for v,n in zip(point,normal))for point in vertices]
    measured_width=max(projections)-min(projections)
    if not math.isclose(measured_width,type_width_feet,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('wall geometry width differs from destination type')
    bottom=min(p[2]for p in vertices);height=max(p[2]for p in vertices)-bottom
    if not math.isclose(bottom,76.0,abs_tol=1e-8):raise ValueError('expected audited Core wall base elevation76')
    dz=base_elevation_feet-bottom;moves=[];planes=lines_count=outlines=0
    for channel,graph in result.items():
        for i,obj in enumerate(graph['objects']):
            name,fields=obj['class_name'],obj['fields'];keys=[]
            if name=='Plane':planes+=1;keys=['m_origin']
            if name=='GLine':lines_count+=1;keys=['m_origin']
            if channel=='101'and name=='Outline':outlines+=1;keys=['m_minmax']
            if channel=='103'and i==0:keys=['m_bBox','m_tightbBox']
            for key in keys:
                old=deepcopy(fields[key]);points=fields[key]if key in ('m_minmax','m_bBox','m_tightbBox')else[fields[key]]
                for point in points:
                    if len(point)!=3 or any(type(v)not in (int,float)or not math.isfinite(v)for v in point):raise ValueError('finite XYZ required')
                    point[2]+=dz
                moves.append({'channel':channel,'object':i,'field':key,'before':old,'after':deepcopy(fields[key])})
    if (planes,lines_count,outlines)!=(14,1,1):raise ValueError('unmeasured wall world-coordinate inventory')
    params=[o for o in result['102']['objects']if o['class_name']=='ParamValueSetDouble']
    if len(params)!=1:raise ValueError('single wall scalar parameter set required')
    byid={p['m_paramId']['m_id']['m_id64']:p for p in params[0]['fields']['m_paramSet']}
    if not all(k in byid for k in (-1001108,-1001109,-1001101)) or byid[-1001108]['m_value']!=0 or not math.isclose(byid[-1001101]['m_value'],height,abs_tol=1e-8):
        raise ValueError('height/base offset cache differs from geometry')
    old=byid[-1001109]['m_value'];offset=height-(top_elevation_feet-base_elevation_feet)
    byid[-1001109]['m_value']=offset
    return result,{'reference_changes':changes,'measured_wall_width_feet':measured_width,'destination_type_width_feet':type_width_feet,
        'base_elevation_feet':base_elevation_feet,'top_level_elevation_feet':top_elevation_feet,'wall_height_feet':height,
        'world_z_delta_feet':dz,'world_coordinate_changes':moves,
        'top_offset_parameter':{'id':-1001109,'before':old,'after':offset},
        'edge_consistency':edge_consistency(result['103'])}


def run(reader,seed,core,profile,target):
    if hashlib.sha256(seed.read_bytes()).hexdigest()!=SEED_SHA or hashlib.sha256(core.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('pinned fixture required')
    if profile['source_sha256']!=SOURCE_SHA or profile['reader_revision']!=REV:raise ValueError('profile provenance mismatch')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    target=target.resolve()
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local')as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-seed-wall-context"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader.resolve()))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-seed-wall-context'
        def probe(*args):return json.loads(subprocess.check_output([str(binary),*map(str,args)]))
        with olefile.OleFileIO(seed)as f:schema=zlib.decompress(unpage(f.openstream('Formats/Latest').read()),31)
        (work/'schema').write_bytes(schema);decl=probe('schema',work/'schema')
        compatible=compare_schemas(profile['declarations'],decl)
        inventory=probe(seed);records={r['identity']['element_id']:r for r in inventory['records']}
        source_material=probe(core,87)['records'][0]
        sm=next(o['fields']for o in source_material['graph']['objects']if o['class_name']=='Material')
        tm=next(o['fields']for o in records[91]['graph']['objects']if o['class_name']=='Material')
        if sm!=tm:raise ValueError('material fields not identical')
        mapping=[]
        for source_id,target_id in EXISTING_MAPPING.items():
            original=next(c for c in profile['context']if c['id']==source_id);r=records[target_id]
            if original['class']!=r['class_name']:raise ValueError('reference class differs')
            root=r['graph']['objects'][0]['fields'];reason='explicit role mapping, geometric/type compatibility guarded separately'
            if r['class_name']=='GStyleElem':
                keys=('m_categoryId','m_gstyleType')
                if any(root[k]!=original['root_fields'][k]for k in keys):raise ValueError('category/style mismatch')
                reason='identical built-in category and graphics-style kind'
            if r['class_name']=='ProjectPhase':
                if root['m_name']!=original['root_fields']['m_name']:raise ValueError('phase name differs')
                reason='matching New Construction phase name'
            if r['class_name']=='MaterialElem':reason='entire embedded Material field object identical'
            mapping.append({'source_id':source_id,'target_id':target_id,'class':r['class_name'],'reason':reason,'source':r['source'],'identity':r['identity']})
        type_record=records[1947];compound=next(o for o in type_record['graph']['objects']if o['class_name']=='CompoundStructure')
        layers=compound['fields']['m_layers'];width=sum(l['m_layerWidth']for l in layers)
        seed_style=next(o['fields']for o in records[119]['graph']['objects']if o['class_name']=='GStyle')
        # Standalone construction check: target level2746 is explicitly planned,
        # not inserted into the seed by this read-only audit.
        from wall_thickness import encode_wall
        _,generated,_=encode_wall(profile,2747,width_feet=width,height_feet=12,length_feet=12,
            translation_xy=(0,0),context=profile['external_references'],yaw_degrees=37,
            room_bounding=False,acknowledge_bounding_hypothesis=True,acknowledge_pending_type_remap=True)
        mapped,remap_audit=remap_graphs(generated,profile['declarations'],EXISTING_MAPPING|{20307:2746},
            new_id=2747,type_width_feet=width)
        encoder=GraphEncoder(profile['declarations']);roundtrips=[]
        for channel,graph in mapped.items():
            body=encoder.graph(graph);(work/'body').write_bytes(body)
            actual=probe('decode',work/'schema',work/'body')
            if actual!=graph:raise ValueError('seed schema independently decoded a different graph')
            roundtrips.append({'channel':int(channel),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),
                'objects':len(graph['objects']),'edges':len(graph['edges']),'complete_seed_schema_roundtrip':True})
        return {'source_sha256':SOURCE_SHA,'seed_sha256':SEED_SHA,'seed_schema_sha256':hashlib.sha256(schema).hexdigest(),
            'reader_revision':REV,'whole_schema_matches_source':hashlib.sha256(schema).hexdigest()==profile['schema_sha256'],'sample_remapped_wall':{'new_id':2747,'planned_upper_level':2746,'file_mutated':False,'roundtrips':roundtrips,'audit':remap_audit},'compatible_classes':compatible,'existing_mapping':mapping,
            'seed_wall_type':{'element_id':1947,'source':type_record['source'],'layer_fields':layers,'width_feet':width,
                'category_material_id':seed_style['m_materialElemId']['m_id']['m_id64']},
            'required_allocations':[{'source_id':20307,'class':'Level','role':'upper level','reason':'seed has only one Level'}],
            'relocation':{'source_base_feet':76.0,'seed_base_feet':0.0,'source_top_feet':91.0,'default_allocated_top_feet':15.0},
            'context_inventory':{'exact_current_records':inventory['summary']['emitted_records'],'unsupported':inventory['summary']['unsupported_graph_records'],
                'off_route':inventory['summary']['current_records_outside_route']},
            'limits':['Source thickness2/3ft differs from seed200mm type; use a separately audited thickness encoder before remapping.',
                'Typed remap plus graph decode does not prove application acceptance or full cache/save lifecycle semantics.',
                'External document pointer token1 and local geometric graph pointers remain unchanged; they are not project ElementIds.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--seed',type=Path,default=Path(__file__).parent/'local/minimal_seed-Project.rvt')
    p.add_argument('--core',type=Path,default=Path(__file__).parent/'local/core2024.rvt')
    p.add_argument('--profile',type=Path,default=Path(__file__).parent/'results/wall-element-profile.json')
    p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/new-element-build/target');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.seed,a.core,json.loads(a.profile.read_text()),a.target),indent=2))
