import copy,json,unittest
from pathlib import Path
from element_properties import set_comments

ROOT=Path(__file__).parent


class ElementPropertiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        profile=json.loads((ROOT/'results/wall-element-profile.json').read_bytes())
        properties=json.loads((ROOT/'results/element-properties.json').read_bytes())
        cls.graph=profile['graphs']['102']
        cls.declarations=profile['declarations']+properties['parameter_declarations']

    def test_explicit_creation_preserves_source_and_changes_only_string_container(self):
        before=copy.deepcopy(self.graph)
        body,objects,report=set_comments(self.graph,self.declarations,'Wall comments 😀',allow_create=True)
        self.assertEqual(self.graph,before)
        self.assertEqual(report['parameter_id'],-1010106)
        self.assertEqual(report['utf16_code_units'],16)
        sets=[o for o in objects if o['class_name']=='ParamValueSetAString']
        self.assertEqual(len(sets),1)
        self.assertEqual(sets[0]['fields']['m_paramSet'][0]['m_value'],'Wall comments 😀')
        self.assertIn('Wall comments 😀'.encode('utf-16-le'),body)
        self.assertFalse(report['arbitrary_application_metadata_supported'])

    def test_missing_creation_consent_invalid_text_and_wrong_profile_rejected(self):
        with self.assertRaises(ValueError):set_comments(self.graph,self.declarations,'text')
        for value in ('a\0b','x'*32768,1):
            with self.assertRaises(ValueError):set_comments(self.graph,self.declarations,value,allow_create=True)
        with self.assertRaises(ValueError):set_comments(self.graph,self.declarations,'text',expected='',allow_create=True)
        graph=copy.deepcopy(self.graph);graph['objects'][0]['class_name']='Other'
        with self.assertRaises(ValueError):set_comments(graph,self.declarations,'text',allow_create=True)

    def test_schema_layout_and_shared_pointer_fail_closed(self):
        declarations=copy.deepcopy(self.declarations)
        next(c for c in declarations if c['name']=='ParamValueAString')['fields'][1]['raw_descriptor']=7
        with self.assertRaises(ValueError):set_comments(self.graph,declarations,'text',allow_create=True)
        graph=copy.deepcopy(self.graph)
        graph['objects'][0]['fields']['m_pParamValueSetAString'].update(pointer_token=2,class_tag=3021)
        with self.assertRaises(ValueError):set_comments(graph,self.declarations,'text',allow_create=True)
