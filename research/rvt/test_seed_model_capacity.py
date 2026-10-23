"""Max-owner request boundary; full saved-file results live in the capacity report."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from seed_model_request import validate
from seed_model_verify import request_oracle

REQUEST=Path(__file__).parent/'results/seed-model-capacity-request.json'

class CapacityTests(unittest.TestCase):
    def test_exact_capacity_and_independent_identity_count(self):
        request=json.loads(REQUEST.read_bytes())
        self.assertEqual(request['levels'],[])
        checked=validate(request);oracle=request_oracle(request)
        self.assertEqual(len(checked['elements']),100)
        self.assertEqual(len(set(e['id']for e in request['elements'])),100)
        self.assertEqual(len(set(e['category']for e in request['elements'])),20)
        self.assertEqual(oracle['expected_new_ids'],list(range(2746,2846)))
        self.assertEqual(sum(len(p['triangles'])for e in request['elements']for p in e['parts']),100)
    def test_101st_owner_rejected_by_both_contracts(self):
        request=json.loads(REQUEST.read_bytes());extra=deepcopy(request['elements'][-1]);extra['id']='capacity-101';request['elements'].append(extra)
        with self.assertRaises(ValueError):validate(request)
        with self.assertRaises(ValueError):request_oracle(request)

if __name__=='__main__':unittest.main()
