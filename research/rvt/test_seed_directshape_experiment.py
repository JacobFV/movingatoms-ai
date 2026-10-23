from copy import deepcopy
import json
from pathlib import Path
import unittest
from seed_directshape_experiment import triangle_key, verify_scene


class SavedMeshChecks(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).parent / 'results'
        self.scene = json.loads((base / 'seed-directshape-scene.json').read_bytes())
        self.request = json.loads((base / 'seed-directshape-request.json').read_bytes())

    def verify(self, scene):
        r = self.request
        return verify_scene(scene, 2746, r['vertices'], r['triangles'], r['config'], {119, 125, 2746})

    def test_real_saved_scene(self):
        self.assertEqual(self.verify(self.scene)['rendered_triangle_count'], 12)
        self.assertIsNone(self.scene['scene']['elements'][0]['meshes']['primitives'][0]['source_owner_id'])

    def test_triangle_key_preserves_winding(self):
        p = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        self.assertEqual(triangle_key(p), triangle_key(p[1:] + p[:1]))
        self.assertNotEqual(triangle_key(p), triangle_key(p[::-1]))

    def test_rejects_rendering_and_identity_corruption(self):
        def primitive(s):
            return s['scene']['elements'][0]['meshes']['primitives'][0]
        def root(s):
            return next(r for r in s['records'] if r['channel'] == 102)['graph']['objects'][0]['fields']
        changes = [
            lambda s: primitive(s)['vertices'][0].__setitem__(0, 900),
            lambda s: primitive(s).__setitem__('source_owner_id', 2746),
            lambda s: primitive(s)['normals'].__setitem__(0, [0, 0, 0]),
            lambda s: s['scene']['elements'][0]['meshes'].__setitem__('rejected_filters', 1),
            lambda s: root(s)['m_id']['m_id'].__setitem__('m_id64', 999999),
            lambda s: root(s)['m_options'].__setitem__('m_AllowsMove', False),
        ]
        for change in changes:
            with self.subTest(change=change):
                altered = deepcopy(self.scene)
                change(altered)
                with self.assertRaises(ValueError):
                    self.verify(altered)


if __name__ == '__main__':
    unittest.main()
