import json
from pathlib import Path
import unittest
from native_mesh import audit_closed,encode_component,l_prism,torus
from native_mesh_intersections import reject_intersections
P=json.loads((Path(__file__).parent/'results/directshape-mesh-profile.json').read_bytes())

class NonconvexTests(unittest.TestCase):
    def test_l_prism(self):
        points,triangles=l_prism()
        with self.assertRaises(ValueError):audit_closed(points,triangles)
        body,fields,report=encode_component(P,points,triangles,allow_nonconvex=True)
        self.assertEqual(report['quantized_geometry']['signed_volume'],3)
        self.assertEqual(report['quantized_geometry']['genus'],0)
        self.assertFalse(report['quantized_geometry']['convex'])
        self.assertEqual(len(fields['m_normalsArr']),20)
    def test_genus_one_torus(self):
        points,triangles=torus()
        report=audit_closed(points,triangles,allow_nonconvex=True)
        self.assertEqual(report['genus'],1)
        self.assertEqual(report['euler_characteristic'],0)
        self.assertGreater(report['signed_volume'],0)
        with self.assertRaises(ValueError):audit_closed(points,[t[::-1]for t in triangles],allow_nonconvex=True)
    def test_crossing_triangles_rejected(self):
        points=[[0,0,0],[2,0,0],[0,2,0],[.5,.5,-1],[.5,.5,1],[1.5,.5,0]]
        with self.assertRaisesRegex(ValueError,'intersect'):reject_intersections(points,[[0,1,2],[3,4,5]],1e-10)
    def test_coplanar_overlap_rejected_even_with_shared_vertex(self):
        points=[[0,0,0],[2,0,0],[0,2,0],[2,2,0],[2,-1,0]]
        with self.assertRaisesRegex(ValueError,'intersect'):reject_intersections(points,[[0,1,2],[0,3,4]],1e-10)
    def test_only_declared_edge_contact_allowed(self):
        points=[[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
        self.assertEqual(reject_intersections(points,[[0,1,2],[1,3,2]],1e-10)['unexpected_intersections'],0)
        # Geometric contact without shared indices is deliberately rejected.
        points += [[1,0,0],[0,1,0]]
        with self.assertRaises(ValueError):reject_intersections(points,[[0,1,2],[4,3,5]],1e-10)
    def test_disconnected_components_rejected(self):
        p,t=l_prism();other=[[x+4,y,z]for x,y,z in p]
        with self.assertRaisesRegex(ValueError,'disconnected'):audit_closed(p+other,t+[[i+len(p)for i in tri]for tri in t],allow_nonconvex=True)

if __name__=='__main__':unittest.main()
