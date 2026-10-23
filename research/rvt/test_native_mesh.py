from copy import deepcopy
import json
import math
from pathlib import Path
import unittest
from native_mesh import encode_component,source_component,cuboid,tetrahedron,audit_closed
P=json.loads((Path(__file__).parent/'results/directshape-mesh-profile.json').read_bytes())

class MeshTests(unittest.TestCase):
    def test_source_exact(self):
        for i in (0,1):
            body,fields,audit=source_component(P,i)
            self.assertTrue(audit['source_exact']);self.assertFalse(audit['closed_solid_claim'])
            self.assertEqual(body[:2],(1732).to_bytes(2,'little'))
    def test_tetrahedron_and_cuboid(self):
        for builder,count,volume in [(tetrahedron,4,1.331),(cuboid,12,7.986)]:
            body,fields,audit=encode_component(P,*builder())
            self.assertEqual(audit['quantized_geometry']['triangles'],count)
            self.assertEqual(len(fields['m_normalsArr']),len(fields['m_facetsArr']))
            self.assertAlmostEqual(audit['original_geometry']['signed_volume'],volume,places=12)
            self.assertLess(audit['volume_error'],1e-6)
            self.assertGreater(audit['maximum_coordinate_error'],0)
            self.assertLess(audit['maximum_coordinate_error'],1e-6)
            self.assertLess(audit['maximum_normal_unit_length_error'],1e-7)
    def test_open_reversed_and_duplicate_triangles_rejected(self):
        points,triangles=cuboid()
        for faces in (triangles[:-1],[t[::-1]for t in triangles],triangles+[triangles[0]]):
            with self.assertRaises(ValueError):audit_closed(points,faces)
    def test_invalid_indices_rejected(self):
        points,triangles=tetrahedron()
        for index in (True,-1,32768,1.5):
            faces=deepcopy(triangles);faces[0][0]=index
            with self.assertRaises(ValueError):encode_component(P,points,faces)
    def test_float32_collapse_rejected(self):
        points,triangles=cuboid(origin=(1e10,1e10,1e10),size=(1,1,1))
        with self.assertRaisesRegex(ValueError,'collapsed'):encode_component(P,points,triangles)
    def test_nonfinite_and_nonconvex_rejected(self):
        points,triangles=cuboid();points[0][0]=float('nan')
        with self.assertRaises(ValueError):encode_component(P,points,triangles)
        points,triangles=cuboid();points[6]=[.5,.5,.5]
        with self.assertRaises(ValueError):encode_component(P,points,triangles)

if __name__=='__main__':unittest.main()
