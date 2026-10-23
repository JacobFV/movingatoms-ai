import json
from copy import deepcopy
from pathlib import Path
import unittest
from seed_wall_context import compare_schemas,remap_graphs,EXISTING_MAPPING
from wall_element import translated_wall
from wall_thickness import encode_wall

class SeedWallContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_text())
    def graphs(self,width=.2/.3048):
        return encode_wall(self.profile,3000,width_feet=width,height_feet=12,length_feet=12,translation_xy=(0,0),context=self.profile['external_references'],yaw_degrees=37,room_bounding=False,acknowledge_bounding_hypothesis=True,acknowledge_pending_type_remap=True)[1]
    def test_seed_remap_geometry_levels_and_no_cascade(self):
        graphs,audit=remap_graphs(self.graphs(),self.profile['declarations'],EXISTING_MAPPING|{20307:2746},new_id=3000,type_width_feet=.2/.3048)
        self.assertEqual(graphs['102']['objects'][0]['fields']['m_assocLevelId']['m_id']['m_id64'],1916)
        self.assertEqual(graphs['102']['objects'][0]['fields']['m_WallAttributesId']['m_id']['m_id64'],1947)
        self.assertEqual(graphs['103']['objects'][0]['fields']['m_GInfo']['m_categoryId']['m_id']['m_id64'],119)
        self.assertEqual(graphs['103']['objects'][0]['fields']['m_bBox'][0][2],0)
        self.assertEqual(audit['top_offset_parameter']['after'],-3)
        self.assertAlmostEqual(audit['measured_wall_width_feet'],.2/.3048)
        self.assertEqual(audit['world_z_delta_feet'],-76)
    def test_mismatched_type_or_collapsed_levels_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'width differs'):
            remap_graphs(self.graphs(),self.profile['declarations'],EXISTING_MAPPING|{20307:2746},new_id=3000,type_width_feet=2/3)
        with self.assertRaisesRegex(ValueError,'distinct'):
            remap_graphs(self.graphs(),self.profile['declarations'],EXISTING_MAPPING|{20307:1916},new_id=3000,type_width_feet=.2/.3048)
    def test_unknown_reference_and_missing_mapping_are_rejected(self):
        graphs=self.graphs();graphs['102']['objects'][0]['fields']['m_famId']['m_id']['m_id64']=99999
        with self.assertRaisesRegex(ValueError,'unmapped'):
            remap_graphs(graphs,self.profile['declarations'],EXISTING_MAPPING|{20307:2746},new_id=3000,type_width_feet=.2/.3048)
        with self.assertRaisesRegex(ValueError,'complete'):
            remap_graphs(self.graphs(),self.profile['declarations'],EXISTING_MAPPING,new_id=3000,type_width_feet=.2/.3048)
        with self.assertRaisesRegex(ValueError,'measured identities'):
            remap_graphs(self.graphs(),self.profile['declarations'],EXISTING_MAPPING|{20307:2746,3:1},new_id=3000,type_width_feet=.2/.3048)
    def test_schema_mismatch_is_rejected(self):
        declarations=deepcopy(self.profile['declarations'])
        self.assertEqual(len(compare_schemas(declarations,declarations)),97)
        declarations[0]['version_like_word']+=1
        with self.assertRaisesRegex(ValueError,'incompatible'):
            compare_schemas(self.profile['declarations'],declarations)
