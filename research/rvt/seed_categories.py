"""Measured minimal-seed category contexts; DirectShape compatibility is unproven."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from schema_probe import REV
from seed_wall_context import SEED_SHA

# Names here connect two public-reader vocabularies; IDs are read from its pinned
# published BuiltInCategory constants and then joined to actual seed records.
CLASS_CONSTANTS={
 'Wall':'OST_WALLS','ArcWall':'OST_WALLS','Door':'OST_DOORS','Window':'OST_WINDOWS',
 'Floor':'OST_FLOORS','BuildingPad':'OST_BUILDING_PAD','Roof':'OST_ROOFS','Ceiling':'OST_CEILINGS',
 'Stair':'OST_STAIRS','StairsRun':'OST_STAIRS_RUNS','StairsLanding':'OST_STAIRS_LANDINGS',
 'StairsStringer':'OST_STAIRS_STRINGER_CARRIAGE','Railing':'OST_STAIRS_RAILING','Ramp':'OST_RAMPS',
 'Column':'OST_COLUMNS','StructuralColumn':'OST_STRUCTURAL_COLUMNS','StructuralFraming':'OST_STRUCTURAL_FRAMING',
 'StructuralFoundation':'OST_STRUCTURAL_FOUNDATION','CurtainWallMullion':'OST_CURTAIN_WALL_MULLIONS',
 'CurtainWallPanel':'OST_CURTAIN_WALL_PANELS','WallSweep':'OST_CORNICES','Room':'OST_ROOMS',
 'Furniture':'OST_FURNITURE','Casework':'OST_CASEWORK','LightingFixture':'OST_LIGHTING_FIXTURES',
 'ElectricalEquipment':'OST_ELECTRICAL_EQUIPMENT','ElectricalFixture':'OST_ELECTRICAL_FIXTURES',
 'MechanicalEquipment':'OST_MECHANICAL_EQUIPMENT','LightingDevice':'OST_LIGHTING_DEVICES',
 'FireAlarmDevice':'OST_FIRE_ALARM_DEVICES','DataDevice':'OST_DATA_DEVICES',
 'PlumbingFixture':'OST_PLUMBING_FIXTURES','SpecialtyEquipment':'OST_SPECIALITY_EQUIPMENT',
 'Duct':'OST_DUCT_CURVES','DuctFitting':'OST_DUCT_FITTING','Pipe':'OST_PIPE_CURVES','PipeFitting':'OST_PIPE_FITTING',
 'Mass':'OST_MASS','GenericModel':'OST_GENERIC_MODEL','DuctTerminal':'OST_DUCT_TERMINAL',
 'FoodServiceEquipment':'OST_FOOD_SERVICE_EQUIPMENT','Planting':'OST_PLANTING','Parking':'OST_PARKING',
 'Entourage':'OST_ENTOURAGE','Hardscape':'OST_HARDSCAPE','VerticalCirculation':'OST_VERTICAL_CIRCULATION',
 'SlabEdge':'OST_EDGE_SLAB'}
ALIASES={'slab':'Floor','beam':'StructuralFraming','generic':'GenericModel','genericmodels':'GenericModel',
         'genericmodel':'GenericModel','stairs':'Stair','walls':'Wall','slabs':'Floor','doors':'Door',
         'windows':'Window','floors':'Floor','columns':'Column','beams':'StructuralFraming','pipes':'Pipe','ducts':'Duct','roofs':'Roof'}


def eid(v):return v['m_id']['m_id64']


def context_for(kind,profile=None,*,interior_policy,explicit_interior_style_id=None,allow_generic_fallback=False):
    """Return source-bound snake_case constructor fields and explicit policy.

    interior_policy: projection, cut, or explicit. Explicit styles may be from
    another category, which is recorded as a caller hypothesis, never inferred.
    """
    if type(allow_generic_fallback)is not bool:raise ValueError('generic fallback must be explicit boolean')
    if profile is None:profile=json.loads((Path(__file__).parent/'results/seed_categories.json').read_text())
    if profile['seed_sha256']!=SEED_SHA or profile['reader_revision']!=REV:raise ValueError('seed category provenance mismatch')
    if profile['seed_schema_sha256']!='0bfb947b3c9a0cec2ea9692873e3b0325f1c9387caaffddbce4cc2509e77cf21':raise ValueError('seed schema mismatch')
    if not isinstance(kind,str)or not kind.strip():raise ValueError('nonempty element kind required')
    canonical={k.lower():k for k in profile['kinds']}
    normalized=kind.strip().lower().replace('_','').replace(' ','')
    selected=ALIASES.get(normalized,canonical.get(normalized));fallback=False
    if selected is None or selected not in profile['kinds']or not profile['kinds'][selected]['available']:
        if not allow_generic_fallback:raise ValueError('unsupported or unavailable category for '+kind)
        selected='GenericModel';fallback=True
    entry=profile['kinds'][selected]
    if not entry['available']:raise ValueError('generic category unavailable')
    styles={s['id']:s for s in profile['styles']};materials={m['id']:m for m in profile['materials']}
    projection=entry['projection_style_id']
    if interior_policy=='projection':interior=projection
    elif interior_policy=='cut':
        interior=entry['cut_style_id']
        if interior is None:raise ValueError('no measured cut style for '+selected)
    elif interior_policy=='explicit':
        if type(explicit_interior_style_id)is not int or explicit_interior_style_id not in styles:raise ValueError('explicit interior style not in seed')
        interior=explicit_interior_style_id
    else:raise ValueError('explicit projection/cut/explicit interior policy required')
    if interior_policy!='explicit'and explicit_interior_style_id is not None:raise ValueError('extraneous explicit interior style')
    for ident in (projection,interior):
        if ident not in styles or styles[ident]['class_name']!='GStyleElem':raise ValueError('style identity missing')
    if styles[projection]['category_id']!=entry['category_id']or styles[projection]['style_kind']!=1:
        raise ValueError('projection category join differs')
    if interior_policy=='cut'and (styles[interior]['category_id']!=entry['category_id']or styles[interior]['style_kind']!=2):raise ValueError('cut category join differs')
    material=styles[interior]['material_id']
    if material!=-1 and (type(material)is not int or material<=0 or material not in materials or materials[material]['class_name']!='MaterialElem'):
        raise ValueError('style material is not a verified seed identity or unassigned sentinel')
    return {'category_id':entry['category_id'],'style_id':projection,'interior_style_id':interior,'material_id':material,
        'requested_kind':kind,'effective_kind':selected,'generic_fallback_used':fallback,'interior_policy':interior_policy,
        'interior_category_id':styles[interior]['category_id'],'cut_style_id':entry['cut_style_id'],
        'ifc_mapping':entry['ifc_mapping'],'seed_sha256':profile['seed_sha256'],
        'native_directshape_category_acceptance':'unproven','material_policy':'measured selected-style material; -1 is unassigned',
        'style_sources':{str(i):styles[i]['source']for i in {projection,interior}}}


def run(reader,seed,target):
    reader=reader.resolve();target=target.resolve()
    if hashlib.sha256(seed.read_bytes()).hexdigest()!=SEED_SHA:raise ValueError('pinned seed required')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    constants_path=reader/'src/partition_element_records.rs';mapping_path=reader/'src/ifc/category_map.rs'
    text=constants_path.read_text();constants={name:int(value.replace('_',''))for name,value in re.findall(r'pub const (OST_\w+): i64 = (-[0-9_]+);',text)}
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local')as directory:
        p=Path(directory);(p/'src').mkdir();(p/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (p/'Cargo.toml').write_text('[package]\nname="rvt-seed-categories"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(p/'Cargo.toml'),'--target-dir',str(target)],check=True)
        result=json.loads(subprocess.check_output([str(target/'release/rvt-seed-categories'),str(seed)]))
    materials=result['materials'];material_ids={m['id']for m in materials};styles=[];bycategory={}
    for r in result['styles']:
        f=r['root_fields'];g=r['style_fields'];m=eid(g['m_materialElemId'])
        material_resolved=m==-1 or m in material_ids
        item={'id':r['id'],'class_name':r['class_name'],'category_id':eid(f['m_categoryId']),
              'material_resolved':material_resolved,'style_kind':f['m_gstyleType'],'owner_id':eid(f['m_ownerId']),'material_id':m,
              'line_pattern_id':eid(g['m_linePatternId']),'color':g['m_color'],'pen_number':g['m_penNumber'],
              'source':r['source'],'unique_id':r['identity']['unique_id']}
        styles.append(item)
        if item['owner_id']==-1:bycategory.setdefault(item['category_id'],{}).setdefault(item['style_kind'],[]).append(item['id'])
    style_index={s['id']:s for s in styles}
    names=dict(result['public_category_names']);mappings={r['revit_class']:r for r in result['public_ifc_mappings']};kinds={}
    for kind,const in CLASS_CONSTANTS.items():
        if const not in constants or kind not in mappings:raise ValueError('public vocabulary mapping absent '+kind)
        category=constants[const];c=bycategory.get(category,{});projection=c.get(1,[]);cut=c.get(2,[])
        available=len(projection)==1 and len(cut)<=1 and style_index[projection[0]]['material_resolved']
        kinds[kind]={'category_id':category,'category_name':names.get(category),'public_constant':const,
            'ifc_mapping':mappings[kind],'available':available,'projection_style_id':projection[0]if len(projection)==1 else None,
            'cut_style_id':cut[0]if len(cut)==1 else None,'diagnostic':None if available else 'missing/ambiguous unowned seed style or unresolved projection material'}
    return {'seed_sha256':SEED_SHA,'reader_revision':REV,'seed_schema_sha256':result['summary']['schema_sha256'],
        'source_files':{str(p.relative_to(reader)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (constants_path,mapping_path)},
        'inventory':result['summary'],'unresolved_material_styles':[s['id']for s in styles if not s['material_resolved']],'kinds':kinds,'styles':styles,'materials':materials,
        'unmapped_public_classes':sorted(set(mappings)-set(kinds)),
        'limits':['Measured category/style existence is not proof that Autodesk accepts DirectShape in that category.',
            'Projection/cut/explicit interior selection is caller policy; no universal native GPolyMesh style default is inferred.',
            'IFC class mappings name public-reader vocabulary; they do not make its IFC exporter support DirectShape.',
            'Material -1 is the saved unassigned sentinel, not an invented positive material identity.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--seed',type=Path,default=Path(__file__).parent/'local/minimal_seed-Project.rvt')
    p.add_argument('--target',type=Path,default=Path(__file__).parent/'local/new-element-build/target');a=p.parse_args()
    print(json.dumps(run(a.reader_source,a.seed,a.target),indent=2))
