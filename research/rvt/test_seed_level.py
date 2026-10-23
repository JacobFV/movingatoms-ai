"""Run: python -m unittest discover -s research/rvt -p test_seed_level.py."""
import hashlib
import json
from pathlib import Path
import unittest
from seed_level import encode_level

ROOT=Path(__file__).parent/'results'

class SeedLevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile=json.loads((ROOT/'seed_level-profile.json').read_bytes())
        cls.report=json.loads((ROOT/'seed_level-audit.json').read_bytes())

    def test_source_exact_and_immutable(self):
        original=json.dumps(self.profile,sort_keys=True)
        bodies=encode_level(self.profile,1916,'Level 1',0,acknowledge_lifecycle_hypothesis=True)
        for channel,body in bodies.items():
            self.assertEqual(hashlib.sha256(body).hexdigest(),self.report['source_channels'][str(channel)]['sha256'])
        self.assertEqual(json.dumps(self.profile,sort_keys=True),original)

    def test_audited_unicode_and_nonzero_variants(self):
        for variant in self.report['variants']:
            bodies=encode_level(self.profile,variant['element_id'],variant['name'],variant['elevation_feet'],acknowledge_lifecycle_hypothesis=True)
            for channel,body in bodies.items():
                self.assertEqual(hashlib.sha256(body).hexdigest(),variant['channels'][str(channel)]['sha256'])

    def test_measured_nonzero_levels_preserve_zero_annotation_points(self):
        controls={c['id']:c for c in self.report['nonzero_level_controls']}
        for ident,z in [(20307,91),(20308,76),(65128,185.5)]:
            item=controls[ident]
            self.assertEqual([v[2] for v in item['plane_origins']],[z,z])
            self.assertEqual(item['bubble_end'],[0,0,0])
            self.assertEqual(item['free_end'],[0,0,0])
            self.assertEqual(item['new_view_reference_points'],[[0,0,0],[0,0,0]])
        mapping=self.report['global_controls'][1]['level_plan_maps'][0]
        self.assertEqual(len(mapping),15)
        self.assertEqual(len(controls),74)
        self.assertEqual(next(x['second']['m_elementIds'] for x in mapping if x['first']['m_id']['m_id64']==65128),[])

    def test_requires_finite_inputs_and_explicit_hypothesis(self):
        with self.assertRaises(ValueError):encode_level(self.profile,2301,'Upper',10)
        for ident,name,z in [(True,'Upper',10),(0,'Upper',10),(2**31,'Upper',10),(2301,'',10),(2301,'A\0B',10),(2301,'Upper',float('inf')),(2301,'Upper',True)]:
            with self.assertRaises(ValueError):encode_level(self.profile,ident,name,z,acknowledge_lifecycle_hypothesis=True)

if __name__=='__main__':unittest.main()
