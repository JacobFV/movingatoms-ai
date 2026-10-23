import copy,json,unittest,uuid
from pathlib import Path
from element_properties_storage import (
    SCHEMA_GUID,SCHEMA_NAME,FIELD_NAMES,schema_definition,
    metadata_values,owner_bodies,register_schema_and_owner)


class OwnStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declarations=json.loads((Path(__file__).parent/'results/new-element-profile.json').read_bytes())['declarations']

    def test_lossless_nested_application_metadata(self):
        properties={'nested':{'flag':True,'missing':None,'number':2.5},'list':['😀',3,'\0']}
        before=copy.deepcopy(properties)
        values=metadata_values('app:42','Wall 😀',properties)
        self.assertEqual(json.loads(values[2]),properties)
        self.assertEqual(properties,before)
        self.assertEqual(metadata_values('app:42','Wall 😀',dict(reversed(list(properties.items())))),values)

    def test_lossy_or_invalid_metadata_rejected(self):
        for properties in ([],{1:'bad'},{'nested':{1:'bad'}},{'tuple':(1,2)}, {'nan':float('nan')},{'inf':float('inf')}):
            with self.subTest(properties=repr(properties)):
                with self.assertRaises(ValueError):metadata_values('app:42','Wall',properties)
        for app,name in (('', 'Wall'),(2,'Wall'),('app',2),('app\0','Wall'),('app','x'*1_000_001)):
            with self.assertRaises(ValueError):metadata_values(app,name,{})

    def test_new_schema_is_independent_and_scalar_strings(self):
        schema=schema_definition()
        self.assertEqual(uuid.UUID(bytes_le=bytes(schema['m_guid']['m_guid']['guid_bytes'])),uuid.UUID(SCHEMA_GUID))
        self.assertEqual(schema['m_schemaName'],SCHEMA_NAME)
        self.assertEqual([r['m_fieldName']for r in schema['m_fields']],list(FIELD_NAMES))
        self.assertTrue(all(r['m_fieldTypeName']=='TCHAR' and r['m_containerType']==0 for r in schema['m_fields']))
        schema['m_fields'][0]['m_fieldName']='mutated'
        self.assertEqual(schema_definition()['m_fields'][0]['m_fieldName'],'ApplicationId')

    def test_owner_and_registration_fail_closed(self):
        bodies=owner_bodies(self.declarations,2746,'app:42','Wall',{'x':'😀'})
        self.assertEqual(set(bodies),{101,102,103})
        for identifier in (0,-1,True,2**31):
            with self.assertRaises(ValueError):owner_bodies(self.declarations,identifier,'app','Wall',{})
        with self.assertRaises(ValueError):register_schema_and_owner(b'',{'objects':[]},[],2746)
