from copy import deepcopy
import json
from pathlib import Path
import unittest
from wall_brep_audit import audit_graph


class NativeBRepAuditTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
        self.graph = deepcopy(self.profile['graphs']['103'])

    def test_native_closed_solid_and_open_sheets(self):
        audit = audit_graph(self.graph)
        self.assertEqual(audit['closed_solids'], 1)
        self.assertAlmostEqual(audit['closed_solid_volume_cubic_feet'], 95, places=8)
        solid = next(g for g in audit['geometry_components'] if g['closed'])
        self.assertEqual((solid['vertices'], solid['edges'], solid['faces'], solid['euler_characteristic']), (8, 12, 6, 2))
        self.assertEqual(len(audit['geometry_components']), 5)
        self.assertTrue(audit['saved_root_bounds_match_native_vertices'])
        # There is deliberately no SWall driver graph input to this verifier.
        self.assertNotIn('GLine', [o['class_name'] for o in self.graph['objects']])

    def test_broken_face_loop_rejected(self):
        edge = self.graph['objects'][16]
        edge['fields']['m_next'][0] = dict(edge['fields']['m_prev'][0])
        with self.assertRaises(ValueError):
            audit_graph(self.graph)

    def test_disconnected_uv_and_nonfinite_plane_rejected(self):
        self.graph['objects'][16]['fields']['m_firstAndLastEdgePnts'][0]['uv'][0][0] += 1
        with self.assertRaisesRegex(ValueError, 'disconnected'):
            audit_graph(self.graph)
        self.graph = deepcopy(self.profile['graphs']['103'])
        self.graph['objects'][50]['fields']['m_origin'][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            audit_graph(self.graph)

    def test_stale_native_bounds_rejected(self):
        self.graph['objects'][0]['fields']['m_tightbBox'][1][0] += 2.5
        with self.assertRaisesRegex(ValueError, 'bounding box differs'):
            audit_graph(self.graph)

    def test_duplicate_topological_face_rejected(self):
        faces = self.graph['objects'][5]['fields']['m_pFaces']
        faces.append(deepcopy(faces[0]))
        with self.assertRaisesRegex(ValueError, 'geometry ownership'):
            audit_graph(self.graph)
