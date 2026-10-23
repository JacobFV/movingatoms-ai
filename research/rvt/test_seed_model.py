import copy,unittest
from seed_model_request import validate
from seed_model import metadata_properties

def request():
 return {'schema_version':1,'units':'metres','levels':[{'id':'basement','name':'Basement Δ','elevation':-3}],
 'elements':[{'id':'mesh-1','name':'Panel Ω','category':'generic','level_id':'basement','properties':{'nested':{'values':[True,None,3.2]}},
 'parts':[{'vertices':[[0,0,-3],[1,0,-3],[0,1,-3]],'triangles':[[0,1,2]]},{'vertices':[[5,0,1],[6,0,1],[5,1,1]],'triangles':[[0,1,2]]}]}]}

class SeedModelTests(unittest.TestCase):
 def test_world_geometry_multipart_and_level_relationship(self):
  r=request();v=validate(r)
  self.assertEqual(v['elements'][0]['parts'],r['elements'][0]['parts'])
  self.assertEqual(v['levels'][0]['elevation'],-3)
  level={'id':'basement','name':'Basement Δ','elevation_m':-3,'element_id':2746}
  props=metadata_properties(v['elements'][0],level)
  self.assertEqual(props['application_properties'],r['elements'][0]['properties'])
  self.assertEqual(props['level']['native_element_id'],2746)
  self.assertNotIn('native_assoc_level_id',props)
 def test_optional_no_levels_and_seed_reuse(self):
  r=request();r['levels']=[];r['elements'][0].pop('level_id')
  self.assertIsNone(validate(r)['elements'][0]['level_id'])
  self.assertIsNone(metadata_properties(validate(r)['elements'][0],None)['level'])
  r=request();r['levels'][0].update(name='Level 1',elevation=0)
  self.assertTrue(validate(r)['levels'][0]['reuse_seed'])
  for name,elevation in [('level 1',0),('Level 1',1)]:
   r['levels'][0].update(name=name,elevation=elevation)
   with self.assertRaises(ValueError):validate(r)
 def test_no_silent_geometry_drop_or_unknown_fields(self):
  for patch in [{'parts':[]},{'parts':[{'vertices':[],'triangles':[]}]},{'level_id':'missing'},{'unexpected':3}]:
   r=request();r['elements'][0].update(patch)
   with self.assertRaises(ValueError):validate(r)
  for face in [[0,1,3],[False,1,2],[0,1]]:
   r=request();r['elements'][0]['parts'][0]['triangles']=[face]
   with self.assertRaises(ValueError):validate(r)
 def test_properties_strict_json_and_nonfinite_geometry(self):
  for props in [{1:'bad'},{'x':float('nan')},{'x':(1,2)},{'x':'\ud800'},{'x':'\0'}]:
   r=request();r['elements'][0]['properties']=props
   with self.assertRaises(ValueError):validate(r)
  r=request();r['elements'][0]['parts'][0]['vertices'][0][0]=float('inf')
  with self.assertRaises(ValueError):validate(r)
 def test_unique_identifiers_and_record_budget(self):
  r=request();r['elements'].append(copy.deepcopy(r['elements'][0]))
  with self.assertRaises(ValueError):validate(r)
  r=request();r['elements']=[{**r['elements'][0],'id':str(i)}for i in range(100)]
  with self.assertRaisesRegex(ValueError,'100 new'):validate(r)

if __name__=='__main__':unittest.main()
