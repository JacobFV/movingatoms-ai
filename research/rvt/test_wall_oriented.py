from copy import deepcopy
import json
import math
from pathlib import Path
import unittest
from wall_oriented import encode_wall, solid_vertices
from wall_parametric import encode_wall as legacy_encode, source_frame
from wall_brep_audit import audit_graph

PROFILE=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())

def encode(angle, length=12, profile=PROFILE):
    return encode_wall(profile,133210,length_feet=length,translation_xy=(400,0),context=profile['external_references'],yaw_degrees=angle,
                       room_bounding=False,acknowledge_bounding_hypothesis=True)

class YawTests(unittest.TestCase):
    def test_zero_preserves_complete_legacy_result(self):
        old=legacy_encode(PROFILE,133210,length_feet=12,translation_xy=(400,0),context=PROFILE['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
        self.assertEqual(encode(0),old)

    def test_rotated_vertices_and_closed_solid(self):
        _,base,_=encode(0); vertices=solid_vertices(base['103']); anchor,_,_=source_frame(PROFILE)
        for angle in (45,90,-30,180,360):
            with self.subTest(angle=angle):
                _,graphs,audit=encode(angle)
                result=audit_graph(graphs['103'])
                actual=solid_vertices(graphs['103']); co,si=math.cos(math.radians(angle)),math.sin(math.radians(angle))
                expected=[]
                for p in vertices:
                    x,y=p[0]-400-anchor[0],p[1]-anchor[1]
                    expected.append([anchor[0]+co*x-si*y+400,anchor[1]+si*x+co*y,p[2]])
                self.assertTrue(all(min(math.dist(v,p) for p in actual)<1e-8 for v in expected))
                self.assertEqual(audit['final_edge_consistency']['paired_face_endpoints_checked'],24)
                self.assertTrue(result['saved_root_bounds_match_native_vertices'])
                self.assertAlmostEqual(result['closed_solid_volume_cubic_feet'],120,places=7)
                solid=next(g for g in result['geometry_components'] if g['closed'])
                self.assertAlmostEqual(solid['surface_area_square_feet'],396,places=7)
                self.assertEqual(graphs['101']['objects'][1]['fields']['m_minmax'],graphs['103']['objects'][0]['fields']['m_bBox'])
                for original,rotated in zip(base['103']['objects'],graphs['103']['objects']):
                    if original['class_name']=='Edge':self.assertEqual(original['fields'],rotated['fields'])
                    if original['class_name']=='Plane':
                        for field in ('m_Envelope','m_orientFlag'):self.assertEqual(original['fields'][field],rotated['fields'][field])

    def test_invalid_angles(self):
        for angle in (True,None,float('nan'),float('inf'),361,-361,'45'):
            with self.subTest(angle=angle),self.assertRaises(ValueError):encode(angle)

    def test_invalid_plane_frame(self):
        profile=deepcopy(PROFILE);profile['graphs']['103']['objects'][50]['fields']['m_xVec']=[2,0,0]
        with self.assertRaises(ValueError):encode(45,profile=profile)

if __name__=='__main__':unittest.main()
