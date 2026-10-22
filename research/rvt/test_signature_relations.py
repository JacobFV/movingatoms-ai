import unittest
from signature_relations import summarize_equal


class RelationTests(unittest.TestCase):
    def test_equal_channel_does_not_claim_equal_message(self):
        rows=[{'key':'same','private':'a','all_channels':'whole-a','location':{'group':0}},
              {'key':'same','private':'b','all_channels':'whole-b','location':{'group':1}},
              {'key':'unique','private':'c','all_channels':'whole-c','location':{'group':2}}]
        result=summarize_equal(rows,'key')
        self.assertEqual(result['duplicate_sets'],1)
        self.assertEqual(result['groups_in_duplicate_sets'],2)
        self.assertEqual(result['sets_with_different_private_fields'],1)
        self.assertTrue(result['examples'][0]['different_complete_inflated_inputs'])

    def test_absent_keys_do_not_create_false_relationship(self):
        rows=[{'key':None},{'key':None}]
        self.assertEqual(summarize_equal(rows,'key')['duplicate_sets'],0)


if __name__=='__main__':unittest.main()
