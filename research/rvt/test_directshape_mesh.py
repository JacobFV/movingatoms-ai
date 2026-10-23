import copy
import json
from pathlib import Path
import unittest
from directshape_mesh import encode_profile

class MeshProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile=json.loads((Path(__file__).parent/'results/directshape-mesh-profile.json').read_text())
    def test_all_measured_records_exact(self):
        self.assertEqual({c:len(b) for c,b in encode_profile(self.profile).items()}, {101:237,102:1732,103:867})
    def test_altered_vertex_rejected(self):
        graph=self.profile['records'][2]['graph']
        obj=next(o for o in graph['objects'] if o['class_name']=='FacetedTopology0')
        obj['fields']['m_pointsArr'][0][0]+=1
        with self.assertRaisesRegex(ValueError,'differs'):encode_profile(self.profile)
    def test_missing_channel_rejected(self):
        self.profile['records'].pop()
        with self.assertRaisesRegex(ValueError,'all channels'):encode_profile(self.profile)

if __name__=='__main__':unittest.main()
