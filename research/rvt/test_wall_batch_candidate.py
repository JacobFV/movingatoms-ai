import json
from pathlib import Path
import tempfile
import unittest
from wall_batch_candidate import DEMO_SPECS, prepare_walls, validate_specs, register_batch, make
from new_element_registration import id_set_bytes
import hashlib

RESULTS = Path(__file__).parent / 'results'

class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads((RESULTS / 'wall-element-profile.json').read_bytes())

    def test_three_distinct_walls(self):
        walls = prepare_walls(self.profile, DEMO_SPECS)
        self.assertEqual([w['id'] for w in walls], [133210,133211,133212])
        for w, length in zip(walls, [6,12,18]):
            self.assertEqual(set(w['bodies']), {101,102,103})
            self.assertAlmostEqual(w['bbox'][1][0]-w['bbox'][0][0], length)

    def test_optional_zero_yaw_preserves_normalization(self):
        self.assertEqual(validate_specs(DEMO_SPECS),validate_specs([dict(s,yaw_degrees=0) for s in DEMO_SPECS]))
        with self.assertRaises(ValueError):validate_specs([DEMO_SPECS[0],dict(DEMO_SPECS[0],yaw_degrees=0)])
        walls=prepare_walls(self.profile,[dict(s,yaw_degrees=a) for s,a in zip(DEMO_SPECS,[45,90,-30])])
        self.assertEqual([w['spec']['yaw_degrees'] for w in walls],[45,90,-30])

    def test_height_defaults_and_changed_bounds(self):
        self.assertEqual(validate_specs(DEMO_SPECS),validate_specs([dict(s,height_feet=15)for s in DEMO_SPECS]))
        walls=prepare_walls(self.profile,[dict(s,height_feet=h)for s,h in zip(DEMO_SPECS,[8,10,20])])
        self.assertEqual([w['bbox'][1][2]-w['bbox'][0][2]for w in walls],[8,10,20])
        for h in (True,0,float('nan'),10001):
            with self.assertRaises(ValueError):validate_specs([dict(DEMO_SPECS[0],height_feet=h)])
        with self.assertRaises(ValueError):validate_specs([DEMO_SPECS[0],dict(DEMO_SPECS[0],height_feet=15)])

    def test_invalid_specs(self):
        for specs in [[], {}, [DEMO_SPECS[0]]*2, [{'length_feet':True,'translation_xy':[400,0]}],
                      [{'length_feet':12,'translation_xy':[float('nan'),0]}],
                      [{'length_feet':float('inf'),'translation_xy':[400,0]}],
                      [{'length_feet':12,'translation_xy':[400,0], 'extra':1}]]:
            with self.subTest(specs=specs), self.assertRaises(ValueError): validate_specs(specs)

    def test_intersection_and_source_clearance(self):
        for specs in [[{'length_feet':12,'translation_xy':[0,0]}],
                      [{'length_feet':12,'translation_xy':[400,0]}, {'length_feet':6,'translation_xy':[405,0]}]]:
            with self.assertRaises(ValueError): prepare_walls(self.profile, specs)

    def test_batch_registration_exact_bytes(self):
        old = [2,20826,40000]; raw = b'abc'+id_set_bytes(old)+b'tail'
        evidence = {'inflated_sha256':hashlib.sha256(raw).hexdigest(), 'object':{
            'class_name':'StructuralElemSetTracking', 'field_spans':[{'name':'m_elemIdSet','start':3,'end':3+len(id_set_bytes(old))}],
            'fields':{'m_elemIdSet':[{'m_id':{'m_id64':v}} for v in old]}}}
        patched, change = register_batch(raw,evidence,[133210,133211,133212])
        self.assertEqual(patched,b'abc'+id_set_bytes(old+[133210,133211,133212])+b'tail')
        self.assertEqual(len(change['ids_after']),6)
        for ids in [[133210,133210],[40000],[True]]:
            with self.assertRaises(ValueError): register_batch(raw,evidence,ids)

    def test_rejected_request_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'missing'/'output'
            with self.assertRaises(ValueError):
                make(Path(tmp)/'absent.rvt',dest,self.profile,[],{},[{'length_feet':float('nan'),'translation_xy':[400,0]}],acknowledge_hypotheses=True)
            self.assertFalse(dest.parent.exists())
            with self.assertRaises(ValueError):
                make(Path(tmp)/'absent.rvt',dest,self.profile,[],{},DEMO_SPECS)
            self.assertFalse(dest.parent.exists())

if __name__=='__main__':unittest.main()
