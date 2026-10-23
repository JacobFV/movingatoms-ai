import tempfile
import unittest
from pathlib import Path
from seed_wall_candidate import checked_specs,make

class SeedWallCandidateTests(unittest.TestCase):
    def test_requires_explicit_hypothesis_acknowledgment(self):
        with self.assertRaisesRegex(ValueError,'acknowledgment'):
            make(Path('/absent'),Path('/unused'),{},{},{},{},[])

    def test_limits_total_allocated_elements_and_rejects_nonfinite_geometry(self):
        with self.assertRaisesRegex(ValueError,'99 walls'):
            checked_specs([{'length_feet':10,'translation_xy':[i*20,0]}for i in range(100)])
        for key,value in [('length_feet',float('nan')),('height_feet',float('inf')),('yaw_degrees',float('nan'))]:
            spec={'length_feet':10,'translation_xy':[0,0],key:value}
            with self.assertRaises(ValueError):checked_specs([spec])
        # Seed has no measured building-instance clearance restriction.
        result=checked_specs([{'length_feet':10,'translation_xy':[-119.5,-67.75],'height_feet':12}])
        self.assertEqual(result[0]['translation_xy'],[-119.5,-67.75])

    def test_wrong_source_fails_before_output(self):
        with tempfile.TemporaryDirectory()as tmp:
            source=Path(tmp)/'wrong.rvt';source.write_bytes(b'not the seed');dest=Path(tmp)/'out'
            with self.assertRaisesRegex(ValueError,'pinned MIT'):
                make(source,dest,{},{},{},{},[{'length_feet':10,'translation_xy':[0,0]}],acknowledge_hypotheses=True)
            self.assertFalse(dest.exists())

if __name__=='__main__':unittest.main()
