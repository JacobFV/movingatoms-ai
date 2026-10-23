import copy,json,tempfile,unittest
from pathlib import Path
from seed_properties_experiment import verify_saved,run

HERE=Path(__file__).parent

class SavedPropertiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual=json.loads((HERE/'results/seed-properties-saved-native.json').read_bytes())
        cls.request={'id':2746,'application_id':'movingatoms:item-42','name':'Application wall 😀',
                     'properties':{'dimensions':{'height_metres':3.2},'enabled':True,'labels':['A','😀'],'optional':None}}

    def test_actual_saved_dynamic_catalog_and_values(self):
        result=verify_saved(self.actual,self.request)
        self.assertTrue(result['dynamic_catalog_discovered_from_saved_file'])
        self.assertTrue(result['application_id_name_properties_exact'])

    def test_wrong_routing_truncation_and_missing_channel_rejected(self):
        for operation in ('routing','truncated','missing'):
            value=copy.deepcopy(self.actual)
            if operation=='routing':value['records'][0]['source']['stream']='Partitions/0'
            if operation=='truncated':value['records'][0]['graph']['consumed_bytes']-=1
            if operation=='missing':value['records'].pop()
            with self.assertRaises(ValueError):verify_saved(value,self.request)

    def test_changed_catalog_and_nested_properties_rejected(self):
        value=copy.deepcopy(self.actual)
        next(iter(value['summary']['extensible_storage_catalog']['schemas'].values()))['raw_metadata']['m_schemaName']='Wrong'
        with self.assertRaises(ValueError):verify_saved(value,self.request)
        request=copy.deepcopy(self.request);request['properties']['dimensions']['height_metres']=9
        with self.assertRaises(ValueError):verify_saved(self.actual,request)

    def test_no_clobber_and_explicit_hypotheses(self):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory)
            with self.assertRaises(ValueError):run(p,p,p,p,p)
            with self.assertRaises(FileExistsError):run(p,p,p,p,p,acknowledge_hypotheses=True)
