"""Small, genuine IfcOpenShell mesh evidence for documentation screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--source-guid',default='2vrSC4nbr48vzSSOTHS45u');p.add_argument('--new-guid',default='25b17ArnDJBg0oqQmFGvy0');a=p.parse_args()
    settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True);rows=[]
    for label,path,guid,ident in [('source',a.source,a.source_guid,20826),('new',a.candidate,a.new_guid,133210)]:
        m=ifcopenshell.open(str(path));wall=m.by_guid(guid);shape=ifcopenshell.geom.create_shape(settings,wall,geometry_library='opencascade');g=shape.geometry
        vertices=list(g.verts);faces=list(g.faces)
        rows.append({'label':label,'file':path.name,'step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_element_id':ident,
                     'ifc_guid':guid,'name':wall.Name,'vertices':[vertices[i:i+3]for i in range(0,len(vertices),3)],
                     'triangles':[faces[i:i+3]for i in range(0,len(faces),3)]})
    print(json.dumps({'kind':'Actual IFC projection meshes, not Revit UI','units':'metres','coordinates':'world',
                      'ifcopenshell_version':ifcopenshell.version,'kernel':'opencascade','meshes':rows,
                      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
