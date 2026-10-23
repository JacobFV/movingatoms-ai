import json
from pathlib import Path
import unittest
from directshape_current import construct
from native_mesh import cuboid

class CurrentShapeTests(unittest.TestCase):
 def setUp(self):
  base=Path(__file__).parent
  self.schema=json.loads((base/'local/directshape-core-schema.json').read_text())
  self.profile=json.loads((base/'results/directshape-mesh-profile.json').read_text())
  legacy=json.loads((base/'results/directshape_legacy_audit.json').read_text())
  self.root=next(r for r in legacy['records']if r['channel']==102)['representatives']['DirectShape']['fields']
  self.config=json.loads((base/'results/directshape_current.json').read_text())['config']
 def call(self,**kwargs):return construct(self.schema,self.profile,self.root,133210,*cuboid(),self.config,**kwargs)
 def test_no_implicit_hypothesis_acceptance(self):
  with self.assertRaisesRegex(ValueError,'acknowledgment'):self.call()
 def test_all_options_explicit(self):
  self.config['options'].pop('m_PresentationType')
  with self.assertRaisesRegex(ValueError,'every DirectShape'):self.call(acknowledge_hypotheses=True)
 def test_boolean_not_enum_integer(self):
  self.config['options']['m_PresentationType']=False
  with self.assertRaisesRegex(ValueError,'option type'):self.call(acknowledge_hypotheses=True)
 def test_three_channels_and_fresh_owner(self):
  bodies,graphs,_=self.call(acknowledge_hypotheses=True)
  self.assertEqual(set(bodies),{101,102,103})
  self.assertEqual(graphs[103]['objects'][0]['fields']['m_elementId'],133210)

if __name__=='__main__':unittest.main()
