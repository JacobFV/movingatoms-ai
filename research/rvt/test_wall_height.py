from copy import deepcopy
import json
from pathlib import Path
import unittest
from wall_height import encode_wall,height_profile
from wall_oriented import encode_wall as oriented
from wall_brep_audit import audit_graph
P=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
KW={'length_feet':12,'translation_xy':[400,0],'context':P['external_references'],'yaw_degrees':45,'room_bounding':False,'acknowledge_bounding_hypothesis':True}

class HeightTests(unittest.TestCase):
    def test_nominal_exact(self):
        self.assertEqual(height_profile(P,15)[0],P)
        self.assertEqual(encode_wall(P,133210,height_feet=15,**KW),oriented(P,133210,**KW))

    def test_constrained_height_and_native_solid(self):
        for height in (8,10,20,25):
            with self.subTest(height=height):
                _,graphs,audit=encode_wall(P,133210,height_feet=height,**KW)
                params=next(o['fields']['m_paramSet'] for o in graphs['102']['objects'] if o['class_name']=='ParamValueSetDouble')
                values={v['m_paramId']['m_id']['m_id64']:v['m_value'] for v in params}
                self.assertEqual(values[-1001109],height-15)
                self.assertEqual(values[-1001101],height)
                self.assertEqual(values[-1001105],8)
                root=graphs['102']['objects'][0]['fields']
                self.assertEqual(root['m_upToLevelId'],P['graphs']['102']['objects'][0]['fields']['m_upToLevelId'])
                measurement=audit_graph(graphs['103'])
                self.assertAlmostEqual(measurement['closed_solid_volume_cubic_feet'],8*height,places=7)
                self.assertAlmostEqual(measurement['native_vertex_bounds_feet'][0][2],76)
                self.assertAlmostEqual(measurement['native_vertex_bounds_feet'][1][2],76+height)
                self.assertEqual(audit['height']['edge_consistency']['paired_face_endpoints_checked'],24)

    def test_bad_heights(self):
        for h in (True,0,-1,float('nan'),float('inf'),10001):
            with self.assertRaises(ValueError):height_profile(P,h)

    def test_unmeasured_constraint_state_rejected(self):
        p=deepcopy(P);p['graphs']['102']['objects'][0]['fields']['m_upToLevelId']['m_id']['m_id64']=-1
        with self.assertRaises(ValueError):height_profile(p,20)
        p=deepcopy(P);o=next(o for o in p['graphs']['102']['objects'] if o['class_name']=='ParamValueSetDouble')
        o['fields']['m_paramSet'][0]['m_value']=1
        with self.assertRaises(ValueError):height_profile(p,20)

if __name__=='__main__':unittest.main()
