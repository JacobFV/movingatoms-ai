import unittest
from wall_batch_verify import validate_specs,expected_bounds,near,DEFAULT_SPECS

class BatchVerificationTests(unittest.TestCase):
    def test_distinct_lengths_and_positions(self):
        validate_specs(DEFAULT_SPECS)
        self.assertEqual([expected_bounds(s)[1][0]-expected_bounds(s)[0][0]for s in DEFAULT_SPECS],[6,12,18])
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):validate_specs([DEFAULT_SPECS[0],DEFAULT_SPECS[0]])
    def test_nonfinite_bounds_rejected(self):
        with self.assertRaises(ValueError):expected_bounds({'length_feet':float('nan'),'translation_xy':[400,0]})
        self.assertFalse(near([float('nan')],[1]))

if __name__=='__main__':unittest.main()
