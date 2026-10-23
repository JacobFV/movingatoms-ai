import json
from pathlib import Path
import unittest
from native_mesh_surface import encode_surface,open_plane,two_components,large_index_surface
P=json.loads((Path(__file__).parent/'results/directshape-mesh-profile.json').read_bytes())

class SurfaceTests(unittest.TestCase):
    def test_open_boundary_and_two_components(self):
        result=encode_surface(P,*open_plane())
        self.assertEqual(result['report']['boundary_edge_count'],4)
        self.assertFalse(result['report']['solid_volume_claim'])
        self.assertEqual(encode_surface(P,*two_components())['report']['edge_connected_component_count'],2)
    def test_exact_welding_and_winding_preserved(self):
        points,triangles=open_plane();points.append(points[0][:]);triangles[1][0]=4
        result=encode_surface(P,points,triangles)
        self.assertEqual(result['report']['input_to_welded_vertex'],[0,1,2,3,0])
        self.assertEqual(result['components'][0]['fields']['m_facetsArr'],[[0,1,2],[0,2,3]])
        triangles[1].reverse();other=encode_surface(P,points,triangles)
        self.assertEqual(other['report']['paired_edge_winding_conflict_count'],1)
    def test_large_signed16_chunk_preserves_every_triangle(self):
        result=encode_surface(P,*large_index_surface())
        self.assertEqual(result['report']['input_vertices'],33000)
        self.assertEqual(result['report']['chunk_count'],2)
        self.assertEqual([c['audit']['vertices']for c in result['components']],[32766,234])
        self.assertEqual(sum(c['audit']['triangles']for c in result['components']),11000)
        self.assertTrue(all(i<=32767 for c in result['components']for tri in c['fields']['m_facetsArr']for i in tri))
    def test_degenerate_duplicate_and_quantization_collapse_rejected(self):
        p,t=open_plane()
        for faces in (t+[[2,1,0]],[[0,0,1]],[[0,1,True]]):
            with self.assertRaises(ValueError):encode_surface(P,p,faces)
        with self.assertRaises(ValueError):encode_surface(P,[[1e10,0,0],[1e10+1,0,0],[1e10,1,0]],[[0,1,2]])
        with self.assertRaises(ValueError):encode_surface(P,p+[[float('nan'),0,0]],t)
    def test_nonmanifold_edge_reported_not_repaired(self):
        points=[[0,0,0],[1,0,0],[0,1,0],[0,-1,0],[0,0,1]]
        result=encode_surface(P,points,[[0,1,2],[1,0,3],[0,1,4]])
        self.assertEqual(result['report']['nonmanifold_edge_count'],1)
        self.assertEqual(result['report']['emitted_triangles'],3)

if __name__=='__main__':unittest.main()
