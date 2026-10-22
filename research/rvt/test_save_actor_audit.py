import json
import unittest
from save_actor_audit import summarize_actor_values


class SaveActorTests(unittest.TestCase):
    def test_empty_username_and_distinct_author_are_not_forced_equal(self):
        result=summarize_actor_values('private-editor',{'Username':'','Author':'application-author'}, {})
        self.assertTrue(result['basic_actor_properties']['Username']['empty'])
        self.assertFalse(result['basic_actor_properties']['Username']['equals_latest_increment_username'])
        self.assertFalse(result['basic_actor_properties']['Author']['equals_latest_increment_username'])
        self.assertEqual(result['xml_author_values'],{})

    def test_equality_reports_do_not_leak_actor_or_path_values(self):
        result=summarize_actor_values('private-editor',{'Username':'private-editor','Last Saved By':'private-editor',
            'Author':'software-identity','Last Save Path':'/private/path/model.rvt'},
            {'{urn:test}entry[0]/{urn:test}author[0]/#text':'private-editor'})
        self.assertEqual(result['all_basic_properties_equal_latest_username'],['Last Saved By','Username'])
        rendered=json.dumps(result)
        for secret in ('private-editor','software-identity','/private/path/model.rvt'):
            self.assertNotIn(secret,rendered)
        xml=next(iter(result['xml_author_values'].values()))
        self.assertTrue(xml['equals_latest_increment_username'])
        self.assertEqual(set(xml['equal_basic_actor_properties']),{'Username','Last Saved By'})
