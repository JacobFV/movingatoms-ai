import unittest
from modification_history import relationships


class ModificationHistoryTests(unittest.TestCase):
    def test_classifies_relationships_without_assuming_user_episode_present(self):
        triples = [(0,0,0), (0,2,0), (0,2,2), (0,3,2), (0,2,0xffffffff)]
        rows = [dict(element_id=i,creation_episode=c,stored_revision=m,other_revision=u)
                for i,(c,m,u) in enumerate(triples)]
        result=relationships(rows,4)
        self.assertEqual(set(result['relationship_counts'].values()), {1})
        self.assertEqual(result['out_of_history_ids'],[4])
        self.assertEqual(result['out_of_history_values'],[
            {'field':'user_modification','value':0xffffffff,'count':1}])

    def test_out_of_range_fields_are_reported_separately(self):
        rows=[dict(element_id=7,creation_episode=3,stored_revision=4,other_revision=5)]
        result=relationships(rows,3)
        self.assertEqual(result['out_of_history_ids'],[7])
        self.assertEqual({v['field'] for v in result['out_of_history_values']},
                         {'creation','modification','user_modification'})
