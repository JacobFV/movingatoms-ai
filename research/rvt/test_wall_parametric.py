from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import unittest
from wall_element import GraphEncoder
from wall_parametric import stretch_profile,encode_wall,source_frame,edge_consistency

PROFILE=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
BASELINE=json.loads((Path(__file__).parent/'results/wall-element.json').read_bytes())

class ParametricWallTests(unittest.TestCase):
    def test_measured_length_reconstructs_all_source_bytes(self):
        restored,audit=stretch_profile(PROFILE,9.5)
        self.assertEqual(restored,PROFILE);self.assertEqual(audit['changes'],[])
        enc=GraphEncoder(restored['declarations'])
        for seq,graph in restored['graphs'].items():
            self.assertEqual(hashlib.sha256(enc.graph(graph)).hexdigest(),BASELINE['channels'][seq]['source_sha256'])

    def test_length_changes_geometry_with_fixed_start_and_section(self):
        bodies,graphs,audit=encode_wall(PROFILE,133210,length_feet=12,translation_xy=(400,0),context=PROFILE['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
        box=graphs['103']['objects'][0]['fields']['m_bBox']
        self.assertAlmostEqual(box[0][0],519.5);self.assertAlmostEqual(box[1][0],531.5)
        self.assertAlmostEqual(box[1][1]-box[0][1],2/3);self.assertAlmostEqual(box[1][2]-box[0][2],15)
        self.assertEqual(audit['final_edge_consistency']['paired_face_endpoints_checked'],24)
        self.assertLess(audit['final_edge_consistency']['maximum_endpoint_disagreement_feet'],1e-10)
        for seq,g in graphs.items():
            self.assertEqual(g['edges'],PROFILE['graphs'][seq]['edges'])
            for a,b in zip(PROFILE['graphs'][seq]['objects'],g['objects']):
                for key in ('m_xVec','m_yVec','m_dirVec','m_controlCommand','m_geomTops'):
                    if key in a['fields']:self.assertEqual(a['fields'][key],b['fields'][key])

    def test_both_sides_of_shared_edges_must_match(self):
        bad=deepcopy(PROFILE)
        edge=next(o for o in bad['graphs']['103']['objects'] if o['class_name']=='Edge' and all(p['pointer_token'] for p in o['fields']['m_pFace']))
        edge['fields']['m_firstAndLastEdgePnts'][0]['uv'][0][0]+=0.1
        with self.assertRaises(ValueError):stretch_profile(bad,12)

    def test_oblique_or_curved_or_patterned_profiles_rejected(self):
        bad=deepcopy(PROFILE)
        plane=next(o for o in bad['graphs']['103']['objects'] if o['class_name']=='Plane')
        plane['fields']['m_xVec']=[math.sqrt(0.5),math.sqrt(0.5),0]
        with self.assertRaises(ValueError):stretch_profile(bad,12)
        bad=deepcopy(PROFILE)
        next(o for o in bad['graphs']['103']['objects'] if o['class_name']=='Edge')['fields']['m_interiorEdgePnts']=[{}]
        with self.assertRaises(ValueError):stretch_profile(bad,12)
        bad=deepcopy(PROFILE)
        next(o for o in bad['graphs']['103']['objects'] if o['class_name']=='GFilling')['fields']['m_patternId']['m_id']['m_id64']=1
        with self.assertRaises(ValueError):stretch_profile(bad,12)

    def test_nonempty_cache_and_extra_lines_rejected(self):
        bad=deepcopy(PROFILE)
        cache=next(o for o in bad['graphs']['102']['objects'] if o['class_name']=='GElement')
        cache['fields']['m_bBox']=[[0,0,0],[1,1,1]]
        with self.assertRaises(ValueError):stretch_profile(bad,12)
        bad=deepcopy(PROFILE)
        line=deepcopy(next(o for o in bad['graphs']['102']['objects'] if o['class_name']=='GLine'))
        bad['graphs']['103']['objects'].append(line)
        with self.assertRaises(ValueError):stretch_profile(bad,12)

    def test_nonfinite_source_and_vacuous_edge_check_rejected(self):
        for field,index in [('m_origin',0),('m_dirVec',0),('m_endParams',0)]:
            bad=deepcopy(PROFILE)
            line=next(o for o in bad['graphs']['102']['objects'] if o['class_name']=='GLine')
            line['fields'][field][index]=float('nan')
            with self.assertRaises(ValueError):stretch_profile(bad,12)
        bad=deepcopy(PROFILE)
        for o in bad['graphs']['103']['objects']:
            if o['class_name']=='Edge':o['fields']['m_pFace'][1]['pointer_token']=0
        with self.assertRaises(ValueError):edge_consistency(bad['graphs']['103'])
        bad=deepcopy(PROFILE)
        edge=next(o for o in bad['graphs']['103']['objects'] if o['class_name']=='Edge')
        edge['fields']['m_firstAndLastEdgePnts'][0]['uv'][0][0]=float('nan')
        with self.assertRaises(ValueError):edge_consistency(bad['graphs']['103'])

    def test_invalid_lengths_rejected(self):
        for length in (True,0,-12,10001,float('inf'),float('nan')):
            with self.assertRaises(ValueError):stretch_profile(PROFILE,length)

    def test_multiple_lengths_preserve_shared_edge_geometry(self):
        for length in (1,6,12,25):
            with self.subTest(length=length):
                changed,audit=stretch_profile(PROFILE,length)
                anchor,axis,new_length=source_frame(changed)
                self.assertAlmostEqual(new_length,length)
                for before,after in zip(audit['fixed_axis_start_feet'],anchor):self.assertAlmostEqual(before,after)
                self.assertLess(edge_consistency(changed['graphs']['103'])['maximum_endpoint_disagreement_feet'],1e-10)

if __name__=='__main__':unittest.main()
