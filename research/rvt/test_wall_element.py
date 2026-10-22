from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from wall_element import GraphEncoder,translated_wall
from new_element_experiment import references

PROFILE=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
EVIDENCE=json.loads((Path(__file__).parent/'results/wall-element.json').read_bytes())

class WallElementTests(unittest.TestCase):
    def test_source_all_three_bodies_exact(self):
        encoder=GraphEncoder(PROFILE['declarations'])
        for seq,graph in PROFILE['graphs'].items():
            self.assertEqual(hashlib.sha256(encoder.graph(graph)).hexdigest(),EVIDENCE['channels'][seq]['source_sha256'])

    def test_translation_moves_world_points_not_directions_or_uv(self):
        bodies,graphs,moves,identities=translated_wall(PROFILE,133210,(30,20),PROFILE['external_references'])
        self.assertEqual(len(identities),4);self.assertEqual(len(moves),18)
        for seq,graph in graphs.items():
            for old,new in zip(PROFILE['graphs'][seq]['objects'],graph['objects']):
                for key in ('m_dirVec','m_xVec','m_yVec','m_Envelope','m_endParams','m_firstAndLastEdgePnts','m_placer'):
                    if key in old['fields']:self.assertEqual(old['fields'][key],new['fields'][key])
            refs=references([o['fields'] for o in graph['objects']])
            self.assertFalse(any(r['id']==20826 for r in refs))
            self.assertTrue(all(r['id']<=0 or r['id']in PROFILE['external_references']+[133210] for r in refs))
            self.assertEqual(hashlib.sha256(bodies[int(seq)]).hexdigest(),EVIDENCE['channels'][seq]['new_sha256'])

    def test_requires_explicit_known_context_and_finite_translation(self):
        for context in ([],PROFILE['external_references']+[999]):
            with self.assertRaises(ValueError):translated_wall(PROFILE,133210,(30,20),context)
        for shift in ((float('inf'),0),(0,float('nan')),(1,2,3)):
            with self.assertRaises(ValueError):translated_wall(PROFILE,133210,shift,PROFILE['external_references'])
        for ident in (20826,0,True,2**31):
            with self.assertRaises(ValueError):translated_wall(PROFILE,ident,(30,20),PROFILE['external_references'])

    def test_boolean_variant_requires_ack_and_changes_only_two_fields(self):
        with self.assertRaises(ValueError):translated_wall(PROFILE,133210,(400,0),PROFILE['external_references'],room_bounding=False)
        normal=translated_wall(PROFILE,133210,(400,0),PROFILE['external_references'])
        variant=translated_wall(PROFILE,133210,(400,0),PROFILE['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
        self.assertEqual(normal[0][101],variant[0][101]);self.assertEqual(normal[0][103],variant[0][103])
        self.assertEqual(sum(a!=b for a,b in zip(normal[0][102],variant[0][102])),2)
        expected=deepcopy(normal[1]);expected['102']['objects'][0]['fields']['m_roomBounding']=False
        next(o for o in expected['102']['objects'] if o['class_name']=='AnalyticalSpaceBoundingCell')['fields']['m_isSpaceBounding']=False
        self.assertEqual(expected,variant[1])

    def test_bad_schema_graph_values_fail_closed(self):
        e=GraphEncoder(PROFILE['declarations']);graph=deepcopy(PROFILE['graphs']['101'])
        graph['objects'][1]['fields']['m_minmax'][0].append(1)
        with self.assertRaises(ValueError):e.graph(graph)
        graph=deepcopy(PROFILE['graphs']['101']);graph['objects'][1]['fields']['m_minmax'][0][0]=float('nan')
        with self.assertRaises(ValueError):e.graph(graph)
        with self.assertRaises(ValueError):GraphEncoder(PROFILE['declarations']+[PROFILE['declarations'][0]])
        declarations=deepcopy(PROFILE['declarations']);declarations[0]['parent_reference']['tag']=declarations[0]['tag']
        with self.assertRaises(ValueError):GraphEncoder(declarations)

if __name__=='__main__':unittest.main()
