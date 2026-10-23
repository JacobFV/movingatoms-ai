from copy import deepcopy
import json
import math
from pathlib import Path
import unittest
from wall_thickness import thickness_profile,encode_wall,SOURCE_WIDTH
from wall_height import encode_wall as height_encode
from wall_oriented import solid_vertices
from wall_brep_audit import audit_graph
P=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
KW={'height_feet':20,'length_feet':12,'translation_xy':[400,0],'context':P['external_references'],'yaw_degrees':45,'room_bounding':False,'acknowledge_bounding_hypothesis':True}

class ThicknessTests(unittest.TestCase):
    def test_source_exact_default(self):
        self.assertEqual(thickness_profile(P,SOURCE_WIDTH)[0],P)
        self.assertEqual(encode_wall(P,133210,**KW),height_encode(P,133210,**KW))
    def test_transverse_width_and_key_offset(self):
        for width in (.2/.3048,.5,1.5):
            with self.subTest(width=width):
                _,graphs,audit=encode_wall(P,133210,width_feet=width,acknowledge_pending_type_remap=True,**KW)
                m=audit_graph(graphs['103'])
                self.assertAlmostEqual(m['closed_solid_volume_cubic_feet'],width*12*20,places=7)
                solid=next(g for g in m['geometry_components']if g['closed'])
                self.assertAlmostEqual(solid['surface_area_square_feet'],2*(12*20+width*12+width*20),places=7)
                points=solid_vertices(graphs['103']);lateral=[(-p[0]+p[1])/math.sqrt(2)for p in points]
                self.assertAlmostEqual(max(lateral)-min(lateral),width,places=7)
                self.assertEqual(graphs['102']['objects'][0]['fields']['m_keyRefOffset'],width/2)
                self.assertTrue(audit['thickness']['requires_existing_type_width_validation'])
    def test_changed_width_needs_type_validation_acknowledgment(self):
        with self.assertRaises(ValueError):encode_wall(P,133210,width_feet=.2/.3048,**KW)
    def test_invalid_width_or_reference_state(self):
        for width in (True,0,-1,float('nan'),float('inf'),11):
            with self.assertRaises(ValueError):thickness_profile(P,width)
        for field,value in [('m_wallKeyRef',0),('m_isFlipped',True),('m_keyRefOffset',0),('m_locLineOffset',1)]:
            p=deepcopy(P);p['graphs']['102']['objects'][0]['fields'][field]=value
            with self.assertRaises(ValueError):thickness_profile(p,.5)

if __name__=='__main__':unittest.main()
