"""Hypothetical current-schema DirectShape mesh bodies, not an accepted RVT save.

Caller must explicitly acknowledge unmeasured instance options, wrapper geometry
flags and lifecycle registration. No implicit native defaults are asserted.
"""
from copy import deepcopy
import hashlib
from directshape_mesh import declarations_for
from native_mesh import encode_component
from wall_element import GraphEncoder

OPTION_FIELDS={'m_PresentationType','m_ReferencingOption','m_RoomBoundingOption','m_AllowsChangeTypeId','m_AllowsCopy','m_AllowsLock','m_AllowsMove','m_AllowsTagAlongCurve'}
HYPOTHESES=[
 '2024 DirectShape option enum values and capability flags are caller choices, not measured instance defaults',
 'identity m_position and null references cell have schema-valid encodings but unmeasured2024 instance lifecycle semantics',
 'legacy typeId=-1/no GeomTable/no GeomSteps structure is portable to2024 only as a hypothesis',
 'terrain GPolyMesh control/flag fields inside DirectShape are unmeasured; closed topology alone does not establish native solid semantics',
 'header flags and parent sets are historical-derived hypotheses; global registration and save allocation are not implemented here']

def construct(schema,mesh_profile,legacy_root,new_id,points,triangles,config,*,acknowledge_hypotheses=False):
 if not acknowledge_hypotheses:raise ValueError('explicit hypothesis acknowledgment required')
 if type(new_id)is not int or not 0<new_id<2**31:raise ValueError('bounded positive fresh element ID required')
 if set(config['options'])!=OPTION_FIELDS:raise ValueError('every DirectShape option must be explicit')
 for name,value in config['options'].items():
  expected=bool if name.startswith('m_Allows')else int
  if type(value)is not expected:raise ValueError('option type differs')
 for key in ('category_id','style_id','interior_style_id','header_flags','can_create_parts_status'):
  if type(config[key])is not int:raise ValueError('explicit integer context required')
 if config['category_id']>=0 or min(config['style_id'],config['interior_style_id'])<=0:raise ValueError('invalid explicit category/style context')
 if any(not isinstance(config[k],str)or not config[k] for k in ('application_id','application_data_id','name')):raise ValueError('fresh application metadata required')
 classes={c['name']:c for c in schema}
 def eid(value):return {'m_id':{'m_id64':value}}
 def ptr(name=None,token=0):return {'class_tag':classes[name]['tag']if name else None,'pointer_token':token}
 def obj(name,fields,token=0):return {'class_name':name,'class_tag':classes[name]['tag'],'token':token,'fields':fields}
 def modern(value):
  if isinstance(value,dict):
   if set(value)=={'m_id'}and type(value['m_id'])is int:return {'m_id64':value['m_id']}
   return {k:modern(v)for k,v in value.items()}
  if isinstance(value,list):return [modern(v)for v in value]
  return value
 root=modern(deepcopy(legacy_root))
 root.update(m_id=eid(new_id),m_oGeometryData=ptr('DirectShapeCell',0xffffffff),m_oShapeData=ptr('DirectShapeDataCell',0xffffffff),
   m_oPlanViewGeometryData=ptr(),m_oRefsData=ptr(),m_options=deepcopy(config['options']),
   m_position={'m_3x3':[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],'m_or':[0.,0.,0.]},m_canCreatePartsStatus=config['can_create_parts_status'])
 _,topology,audit=encode_component(mesh_profile,points,triangles);bounds=audit['quantized_geometry']['bounds']
 source=next(r for r in mesh_profile['records']if r['channel']==103)['graph']['objects']
 ge=deepcopy(source[0]['fields']);ge.update(m_bBox=bounds,m_tightbBox=bounds,m_elementId=new_id,m_subNodes=[ptr('GPolyMesh',4)])
 ge['m_GInfo'].update(m_categoryId=eid(config['style_id']),m_tag=new_id)
 mesh=deepcopy(next(o for o in source if o['class_name']=='GPolyMesh')['fields']);mesh.update(m_interiorGStyleID=eid(config['interior_style_id']),m_pFacetedTopology=ptr('FacetedTopology0',0xffffffff))
 graph102={'objects':[obj('DirectShape',root),obj('DirectShapeCell',{'m_oGElement':ptr('GElement',3)},0xffffffff),
  obj('DirectShapeDataCell',{'m_appGUID':config['application_id'],'m_appDataGUID':config['application_data_id'],'m_name':config['name'],'m_categoryId':eid(config['category_id'])},0xffffffff),
  obj('GElement',ge,3),obj('GPolyMesh',mesh,4),obj('FacetedTopology0',topology,0xffffffff)]}
 ge103=deepcopy(ge);ge103['m_subNodes']=[ptr('GPolyMesh',3)]
 graph103={'objects':[obj('GElement',ge103),obj('GPolyMesh',deepcopy(mesh),3),obj('FacetedTopology0',deepcopy(topology),0xffffffff)]}
 header=deepcopy(mesh_profile['records'][0]['graph']['objects'])
 header[0]['fields'].update(m_abFlags4Bytes=config['header_flags'],m_categroryId=eid(config['category_id']),m_classDef={'m_ref':{'class_tag':classes['DirectShape']['tag'],'class_name':'DirectShape'}})
 header[1]['fields']['m_minmax']=bounds
 parents=header[2]['fields']
 for key,value in parents.items():
  if isinstance(value,list):parents[key]=[]
 parents['m_deletion']=[eid(i)for i in sorted(set([config['category_id'],config['style_id'],config['interior_style_id'],new_id]))]
 graph101={'objects':header}
 graphs={101:graph101,102:graph102,103:graph103};bodies={}
 for channel,graph in graphs.items():bodies[channel]=GraphEncoder(declarations_for(graph,schema)).graph(graph)
 return bodies,graphs,{'new_element_id':new_id,'config':config,'hypotheses':HYPOTHESES,'mesh':audit,'body_sha256':{c:hashlib.sha256(b).hexdigest()for c,b in bodies.items()},'document_created':False,'global_registration_implemented':False,'autodesk_acceptance':'not_tested'}
