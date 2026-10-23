"""Explicit-hypothesis multi-mesh DirectShape bodies; source coordinates in metres."""
from copy import deepcopy
import hashlib
import math
from directshape_current import construct as closed_scaffold
from directshape_mesh import declarations_for
from native_mesh import cuboid
from wall_element import GraphEncoder

FEET_PER_METRE=1/0.3048


def metres_to_feet(points):
 if any(len(p)!=3 or any(type(v)not in(int,float)or not math.isfinite(v)for v in p)for p in points):raise ValueError('finite metre XYZ triples required')
 return [[v/0.3048 for v in point]for point in points]


def construct_components(schema,mesh_profile,legacy_root,new_id,components,config,*,acknowledge_hypotheses=False):
 """Wrap explicit topology components. Allocation/registration remains external."""
 if not components:raise ValueError('at least one surface component required')
 # Reuse the validated header/instance scaffold, replacing every geometry object
 # and discarding its temporary closed-solid audit before emitting any body.
 _,graphs,report=closed_scaffold(schema,mesh_profile,legacy_root,new_id,*cuboid(),config,acknowledge_hypotheses=acknowledge_hypotheses)
 byname={c['name']:c for c in schema};mesh_tag=byname['GPolyMesh']['tag'];topo_tag=byname['FacetedTopology0']['tag']
 for component in components:
  fields=component['fields'];points=fields['m_pointsArr'];triangles=fields['m_facetsArr']
  if not points or not triangles:raise ValueError('empty mesh component')
  if len(fields['m_normalsArr'])!=len(triangles):raise ValueError('per-triangle normals required')
  if any(len(t)!=3 or any(type(i)is not int or not 0<=i<len(points)or i>32767 for i in t)for t in triangles):raise ValueError('invalid component triangle')
 bounds=[[min(p[i]for c in components for p in c['fields']['m_pointsArr'])for i in range(3)],
         [max(p[i]for c in components for p in c['fields']['m_pointsArr'])for i in range(3)]]
 template=deepcopy(graphs[103]['objects'][1])
 if 'material_id' in config:
  material=config['material_id']
  if type(material)is not int or material==0 or material < -1:raise ValueError('positive material ID or -1 sentinel required')
  template['fields']['m_materialID']={'m_id':{'m_id64':material}}
  if material>0:
   parents=graphs[101]['objects'][2]['fields']['m_deletion']
   if material not in [p['m_id']['m_id64']for p in parents]:parents.append({'m_id':{'m_id64':material}})
   parents.sort(key=lambda p:p['m_id']['m_id64'])
 def geometry(root,first_token):
  root=deepcopy(root);root['fields'].update(m_bBox=bounds,m_tightbBox=bounds,
   m_subNodes=[{'class_tag':mesh_tag,'pointer_token':first_token+i}for i in range(len(components))])
  meshes=[];topologies=[]
  for i,component in enumerate(components):
   mesh=deepcopy(template);mesh['token']=first_token+i;mesh['fields']['m_GInfo']['m_tag']=i
   mesh['fields']['m_pFacetedTopology']={'class_tag':topo_tag,'pointer_token':0xffffffff}
   meshes.append(mesh);topologies.append({'class_name':'FacetedTopology0','class_tag':topo_tag,'token':0xffffffff,'fields':deepcopy(component['fields'])})
  return [root]+meshes+topologies
 graphs[101]['objects'][1]['fields']['m_minmax']=bounds
 graphs[102]['objects']=graphs[102]['objects'][:3]+geometry(graphs[102]['objects'][3],4)
 graphs[103]['objects']=geometry(graphs[103]['objects'][0],3)
 bodies={channel:GraphEncoder(declarations_for(graph,schema)).graph(graph)for channel,graph in graphs.items()}
 report.pop('mesh');report['body_sha256']={str(c):hashlib.sha256(b).hexdigest()for c,b in bodies.items()}
 report.update(scope='Multi-component mesh surface bodies; no closed-solid assertion, document or registration',
  component_count=len(components),triangle_count=sum(len(c['fields']['m_facetsArr'])for c in components),
  bounds_feet=bounds,component_audits=[c['audit']for c in components],
  normals_contract='one outward/oriented source-face normal per triangle; surface winding is input-defined')
 return bodies,graphs,report


def construct_metres(schema,mesh_profile,legacy_root,new_id,points_metres,triangles,config,*,chunk_vertex_limit=32768,acknowledge_hypotheses=False):
 from native_mesh_surface import encode_surface
 feet=metres_to_feet(points_metres)
 encoded=encode_surface(mesh_profile,feet,triangles,chunk_vertex_limit=chunk_vertex_limit)
 bodies,graphs,report=construct_components(schema,mesh_profile,legacy_root,new_id,encoded['components'],config,acknowledge_hypotheses=acknowledge_hypotheses)
 report.update(input_units='metres',native_units='feet',metres_per_foot=0.3048,
  input_points_metres=deepcopy(points_metres),input_triangles=deepcopy(triangles),surface=encoded['report'])
 return bodies,graphs,report,encoded['components']
