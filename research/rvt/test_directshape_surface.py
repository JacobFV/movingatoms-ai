import json
from pathlib import Path
import unittest
from directshape_surface import construct_metres,metres_to_feet

class SurfaceWrapperTests(unittest.TestCase):
 def setUp(self):
  b=Path(__file__).parent
  self.schema=json.loads((b/'local/directshape-core-schema.json').read_text())
  self.profile=json.loads((b/'results/directshape-mesh-profile.json').read_text())
  legacy=json.loads((b/'results/directshape_legacy_audit.json').read_text())
  self.root=next(r for r in legacy['records']if r['channel']==102)['representatives']['DirectShape']['fields']
  self.config=json.loads((b/'results/directshape_current.json').read_text())['config']
 def test_units(self):self.assertEqual(metres_to_feet([[.3048,.6096,0]]),[[1,2,0]])
 def test_nonfinite_rejected(self):
  with self.assertRaisesRegex(ValueError,'finite'):metres_to_feet([[float('nan'),0,0]])
 def test_multiple_open_parts_keep_all_triangles(self):
  points=[[0,0,0],[.3048,0,0],[0,.3048,0],[1,0,0],[2,0,0],[1,1,0]]
  bodies,graphs,audit,components=construct_metres(self.schema,self.profile,self.root,2746,points,[[0,1,2],[3,4,5]],self.config,chunk_vertex_limit=3,acknowledge_hypotheses=True)
  self.assertEqual(set(bodies),{101,102,103});self.assertEqual(audit['triangle_count'],2);self.assertEqual(len(components),2)
  self.assertEqual(components[0]['fields']['m_pointsArr'][1],[1.,0.,0.]);self.assertEqual(graphs[103]['objects'][0]['fields']['m_elementId'],2746)
 def test_explicit_material_binding(self):
  self.config['material_id']=91
  _,graphs,_,_=construct_metres(self.schema,self.profile,self.root,2746,[[0,0,0],[1,0,0],[0,1,0]],[[0,1,2]],self.config,acknowledge_hypotheses=True)
  for channel in(102,103):
   mesh=next(o for o in graphs[channel]['objects']if o['class_name']=='GPolyMesh')
   self.assertEqual(mesh['fields']['m_materialID']['m_id']['m_id64'],91)
  self.assertIn(91,[v['m_id']['m_id64']for v in graphs[101]['objects'][2]['fields']['m_deletion']])
 def test_hypothesis_opt_in_required(self):
  with self.assertRaisesRegex(ValueError,'acknowledgment'):construct_metres(self.schema,self.profile,self.root,2746,[[0,0,0],[1,0,0],[0,1,0]],[[0,1,2]],self.config)

if __name__=='__main__':unittest.main()
