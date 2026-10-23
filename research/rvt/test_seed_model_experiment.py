import unittest
from seed_model_experiment import bind_transport,validate_bindings,verify_plan_metadata

class PipelineBindingTests(unittest.TestCase):
 def test_transport_must_bind_both_files(self):
  for value in ({},{'input_sha256':'source','output_sha256':'wrong'},{'input_sha256':'wrong','output_sha256':'candidate'}):
   with self.assertRaisesRegex(ValueError,'transport'):bind_transport(value,'source','candidate')
  self.assertEqual(bind_transport({'input_sha256':'source','output_sha256':'candidate'},'source','candidate')['candidate_sha256'],'candidate')
 def test_no_cross_candidate_or_missing_evidence(self):
  for rows in ([],[{}],[{'source_sha256':'wrong','candidate_sha256':'candidate'}],[{'source_sha256':'source','candidate_sha256':'wrong'}]):
   with self.assertRaisesRegex(ValueError,'all reports'):validate_bindings(rows,'source','candidate')
 def test_actual_body_inventory_matches_plan(self):
  plan={'expected_new_ids':[10],'levels':[],'elements':[{'element_id':10,'body_sha256':{'101':'hash'}}]}
  metadata={'table':{'new_ids':[10]},'body_sha256':{'101':{'10':'hash'}}}
  verify_plan_metadata(plan,metadata);metadata['body_sha256']['101']['10']='changed'
  with self.assertRaisesRegex(ValueError,'saved body'):verify_plan_metadata(plan,metadata)

if __name__=='__main__':unittest.main()
