import unittest
from wall_parametric_candidate_ifc import check_dimensions

class ParametricShapeTests(unittest.TestCase):
    def test_expected_twelve_foot_wall(self):
        dims=[12.,2/3,15.];m=[x*.3048 for x in dims]
        self.assertAlmostEqual(check_dimensions([0,0,0],m,m[0]*m[1]*m[2],dims)['dimensions_metres'][0],3.6576)
    def test_nonfinite_geometry_rejected(self):
        with self.assertRaises(ValueError):check_dimensions([float('nan'),0,0],[1,1,1],1,[1,1,1])
    def test_old_length_and_wrong_volume_rejected(self):
        with self.assertRaises(ValueError):check_dimensions([0,0,0],[9.5*.3048,2/3*.3048,15*.3048],1,[12,2/3,15])
        with self.assertRaises(ValueError):check_dimensions([0,0,0],[12*.3048,2/3*.3048,15*.3048],1,[12,2/3,15])

if __name__=='__main__':unittest.main()
