"""IfcOpenShell STEP schema and actual wall triangulation validation (SI metres).

Use isolated local ifc-validation-env; never reports RVT acceptance.
"""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import ifcopenshell.validate
import numpy as np


def run(source,candidate,new_guid,translation=(30.0,20.0)):
    reports=[];meshes=[];schema_reports=[];models=[];settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True)
    for path in (source,candidate):
        model=ifcopenshell.open(str(path));models.append(model);logger=ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(model,logger,express_rules=True)
        errors=[{'level':s.get('level'),'message':s.get('message'),'instance':str(s.get('instance'))}for s in logger.statements]
        schema_reports.append({'file':path.name,'schema':model.schema,'unit_scale_to_metres':ifcopenshell.util.unit.calculate_unit_scale(model),
                               'validation_messages':len(errors),'levels':dict(Counter(s['level']for s in errors)),'messages':errors})
        rows={};data={}
        for wall in model.by_type('IfcWall'):
            if wall.GlobalId in rows:raise ValueError('duplicate wall GUID')
            shape=ifcopenshell.geom.create_shape(settings,wall,geometry_library='opencascade');g=shape.geometry
            vertices=np.asarray(g.verts).reshape((-1,3));faces=list(g.faces)
            rows[wall.GlobalId]={'name':wall.Name,'minimum_metres':vertices.min(axis=0).tolist(),'maximum_metres':vertices.max(axis=0).tolist(),
                                'volume_cubic_metres':ifcopenshell.util.shape.get_volume(g),'vertices':len(vertices),'triangles':len(faces)//3}
            data[wall.GlobalId]=(vertices,faces)
        meshes.append(data);reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'walls':rows})
    old,new=[r['walls']for r in reports]
    if set(new)!=set(old)|{new_guid}:raise ValueError('unexpected IFC wall GUID inventory')
    for guid in old:
        if old[guid]!=new[guid] or not np.array_equal(meshes[0][guid][0],meshes[1][guid][0])or meshes[0][guid][1]!=meshes[1][guid][1]:
            raise ValueError('existing IFC wall triangulation changed')
    matches=[g for g,v in old.items()if v['name'].endswith(':20826')]
    if len(matches)!=1:raise ValueError('ambiguous source wall')
    source_guid=matches[0];a=old[source_guid];b=new[new_guid];tol=1e-8;shift=np.asarray([translation[0]*.3048,translation[1]*.3048,0])
    for field in ('minimum_metres','maximum_metres'):
        if not np.allclose(np.asarray(a[field])+shift,b[field],atol=tol,rtol=0):raise ValueError('new mesh translation incorrect')
    if abs(a['volume_cubic_metres']-b['volume_cubic_metres'])>tol:raise ValueError('new volume differs')
    if (a['vertices'],a['triangles'])!=(b['vertices'],b['triangles']):raise ValueError('new mesh topology size differs')
    normalized=meshes[1][new_guid][0]-shift;original=meshes[0][source_guid][0]
    if not np.allclose(normalized[np.lexsort(normalized.T[::-1])],original[np.lexsort(original.T[::-1])],atol=tol,rtol=0):raise ValueError('new mesh vertex coordinates differ')
    def association(element):
        rels=[r for r in element.HasAssociations if r.is_a('IfcRelAssociatesMaterial')]
        if len(rels)!=1:raise ValueError('expected one wall material association')
        mat=rels[0].RelatingMaterial
        if mat.is_a('IfcMaterial'):return {'kind':mat.is_a(),'materials':[mat.get_info()],'layer_thickness_metres':None}
        if mat.is_a('IfcMaterialLayerSetUsage'):
            layers=mat.ForLayerSet.MaterialLayers
            return {'kind':mat.is_a(),'materials':[l.Material.get_info()for l in layers],
                    'layer_thickness_metres':sum(l.LayerThickness for l in layers),
                    'layer_set_name':mat.ForLayerSet.LayerSetName,'layer_direction':mat.LayerSetDirection,'direction_sense':mat.DirectionSense,
                    'offset_from_reference_line_metres':mat.OffsetFromReferenceLine}
        raise ValueError('unsupported material association')
    source_material=association(models[1].by_guid(source_guid));new_material=association(models[1].by_guid(new_guid))
    material={'source':source_material,'new':new_material,'same_exact_material_entities':source_material['materials']==new_material['materials'],
              'new_layer_total_matches_wall_mesh_thickness':bool(abs(new_material['layer_thickness_metres']-min(np.asarray(b['maximum_metres'])-np.asarray(b['minimum_metres'])))<=tol)}
    return {'ifcopenshell_version':ifcopenshell.version,'python_version':platform.python_version(),
            'installed_dependencies':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'geometry_kernel':'opencascade','geometry_units':'metres',
            'coordinate_tolerance_metres':tol,'volume_tolerance_cubic_metres':tol,'schema_validation':schema_reports,
            'source_sha256':reports[0]['sha256'],'candidate_sha256':reports[1]['sha256'],
            'existing_wall_meshes_exactly_preserved':len(old),'new_wall_count':len(new),
            'source_wall_guid':source_guid,'new_wall_guid':new_guid,'source_wall':a,'new_wall':b,
            'translation_metres':shift.tolist(),'material_association_comparison':material,'new_mesh_translation_and_volume_verified':True,
            'documentation':'https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html','autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--new-guid',required=True);p.add_argument('--translation',type=float,nargs=2,default=(30.0,20.0));a=p.parse_args()
    print(json.dumps(run(a.source,a.candidate,a.new_guid,a.translation),indent=2))
