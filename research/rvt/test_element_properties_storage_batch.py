import copy,hashlib,json,unittest
from pathlib import Path
from element_properties_storage_batch import attach,register_schema_and_owners
from element_properties import declarations_for
from wall_element import GraphEncoder

HERE=Path(__file__).parent
class AttachedPropertiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wall=json.loads((HERE/'results/wall-element-profile.json').read_bytes())
        storage=json.loads((HERE/'results/new-element-profile.json').read_bytes())
        cls.graph=wall['graphs']['102']
        cls.declarations=list({c['tag']:c for c in wall['declarations']+storage['declarations']}.values())
        cls.body=GraphEncoder(declarations_for(cls.declarations,[cls.graph])).graph(cls.graph)

    def test_real_wall_control_matches_independent_audit(self):
        source=copy.deepcopy(self.graph)
        body,report=attach(self.graph,self.declarations,self.body,'movingatoms:attached-20826','SWall attached',
            {'nested':{'height':3.2},'tags':['test','😀'],'enabled':True},acknowledge_hypotheses=True)
        self.assertEqual(self.graph,source)
        self.assertFalse(report['original_cell_list_was_null'])
        audit=json.loads((HERE/'results/element-properties-storage-batch.json').read_bytes())
        trial=next(r for r in audit['trials']if r['owner_class']=='SWall')
        self.assertEqual(hashlib.sha256(body).hexdigest(),trial['attached_body_sha256'])

    def test_source_mutation_missing_consent_and_unreachable_objects_rejected(self):
        with self.assertRaises(ValueError):attach(self.graph,self.declarations,self.body,'app','name',{})
        with self.assertRaises(ValueError):attach(self.graph,self.declarations,self.body+b'X','app','name',{},acknowledge_hypotheses=True)
        graph=copy.deepcopy(self.graph);graph['edges']=[]
        with self.assertRaises(ValueError):attach(graph,self.declarations,self.body,'app','name',{},acknowledge_hypotheses=True)

    def test_batch_ids_explicit_sorted_distinct(self):
        for ids in ([],[1,1],[2,1],[True],[-1],[2**31],(1,2)):
            with self.subTest(ids=ids):
                with self.assertRaises(ValueError):register_schema_and_owners(b'',{'objects':[]},[],ids)
