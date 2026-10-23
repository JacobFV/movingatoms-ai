"""Independent STEP geometry checks for bounded parametric wall experiments."""
import hashlib
import json
import math
from pathlib import Path


def check_dimensions(minimum,maximum,volume,expected_dimensions_feet,tolerance=1e-8):
    if any(not math.isfinite(v)for v in [*minimum,*maximum,volume,*expected_dimensions_feet,tolerance])or tolerance<=0:
        raise ValueError('finite geometry and positive tolerance required')
    expected=[v*.3048 for v in expected_dimensions_feet]
    dimensions=[b-a for a,b in zip(minimum,maximum)]
    if len(minimum)!=3 or len(maximum)!=3 or len(expected)!=3:raise ValueError('three dimensions required')
    if any(abs(a-b)>tolerance for a,b in zip(dimensions,expected)):raise ValueError('parametric mesh dimensions differ')
    expected_volume=expected[0]*expected[1]*expected[2]
    if abs(volume-expected_volume)>tolerance:raise ValueError('parametric mesh volume differs')
    return {'dimensions_metres':dimensions,'expected_dimensions_metres':expected,
            'volume_cubic_metres':volume,'expected_volume_cubic_metres':expected_volume,
            'coordinate_tolerance_metres':tolerance,'volume_tolerance_cubic_metres':tolerance}


def verify(source,candidate,new_guid,expected_dimensions_feet,expected_minimum_metres):
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    import ifcopenshell.validate
    import numpy as np
    settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True)
    models=[];meshes=[];schemas=[]
    for path in (source,candidate):
        model=ifcopenshell.open(str(path));models.append(model)
        logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(model,logger,express_rules=True)
        schemas.append({'file':path.name,'messages':[{'level':s.get('level'),'message':s.get('message'),'instance':str(s.get('instance'))}for s in logger.statements]})
        rows={}
        for wall in model.by_type('IfcWall'):
            if wall.GlobalId in rows:raise ValueError('duplicate native IFC GUID')
            shape=ifcopenshell.geom.create_shape(settings,wall,geometry_library='opencascade');g=shape.geometry
            rows[wall.GlobalId]=(np.asarray(g.verts).reshape((-1,3)),list(g.faces),ifcopenshell.util.shape.get_volume(g))
        meshes.append(rows)
    old,new=meshes
    if set(new)!=set(old)|{new_guid}:raise ValueError('unexpected parametric wall inventory')
    for guid,(vertices,faces,volume)in old.items():
        if not np.array_equal(new[guid][0],vertices)or new[guid][1]!=faces or new[guid][2]!=volume:
            raise ValueError('old IFC wall mesh changed')
    vertices,faces,volume=new[new_guid];minimum=vertices.min(axis=0).tolist();maximum=vertices.max(axis=0).tolist()
    shape=check_dimensions(minimum,maximum,volume,expected_dimensions_feet)
    if not np.allclose(minimum,expected_minimum_metres,atol=1e-8,rtol=0):raise ValueError('parametric wall placement differs')
    if len(vertices)!=8 or len(faces)!=36:raise ValueError('expected rectangular wall mesh topology')
    wall=models[1].by_guid(new_guid)
    rels=[r for r in wall.HasAssociations if r.is_a('IfcRelAssociatesMaterial')]
    if len(rels)!=1 or not rels[0].RelatingMaterial.is_a('IfcMaterialLayerSetUsage'):raise ValueError('missing material layer usage')
    layers=rels[0].RelatingMaterial.ForLayerSet.MaterialLayers
    if len(layers)!=1 or layers[0].Material.Name!='Default Wall' or abs(layers[0].LayerThickness-expected_dimensions_feet[1]*.3048)>1e-8:
        raise ValueError('parametric material/thickness differs')
    return {'source_ifc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_ifc_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'ifcopenshell_version':ifcopenshell.version,'kernel':'opencascade','units':'metres','schema_validation':schemas,
            'unchanged_existing_wall_meshes':len(old),'candidate_wall_count':len(new),'new_native_ifc_guid':new_guid,
            'minimum_metres':minimum,'maximum_metres':maximum,'vertices':8,'triangles':12,'shape':shape,
            'material':{'name':layers[0].Material.Name,'thickness_metres':layers[0].LayerThickness},
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'autodesk_acceptance':'not_tested',
            'validation_scope':'Actual emitted IFC triangulation; exporter may derive extrusion from wall drivers. This does not independently validate the native BRep.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--new-guid',default='25b17ArnDJBg0oqQmFGvy0');p.add_argument('--correct-owner-history',action='store_true');a=p.parse_args()
    changes=[];source,candidate=a.source,a.candidate
    if a.correct_owner_history:
        from wall_candidate_ifc_owner_control import correct
        outputs=[path.with_name(path.stem+'-owner-corrected.ifc')for path in(source,candidate)]
        changes=[correct(path,out)for path,out in zip((source,candidate),outputs)];source,candidate=outputs
    result=verify(source,candidate,a.new_guid,[12,2/3,15],[519.5*.3048,67.41666666666663*.3048,76*.3048])
    if changes:
        if any(row['messages']for row in result['schema_validation']):raise ValueError('corrected parametric export has schema errors')
        result['explicit_owner_history_correction_controls']=changes
    print(json.dumps(result,indent=2))
