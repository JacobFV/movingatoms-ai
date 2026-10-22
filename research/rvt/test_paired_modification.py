import copy
import unittest
from paired_modification import compare


class PairedModificationTests(unittest.TestCase):
    def snapshot(self):
        return {'path':'test.rvt','sha256':'test','episodes':(b'episode',),
                'rows':{1:{'unique_id':'id','creation':0,'modification':0,'user_modification':0,
                           'selected_increment':0,'selection_reason':'exact_episode_route',
                           'bodies':{101:'a',102:'b',103:'c'}}},
                'increment_fields':{'m_increments':[{'m_greatest':{'m_id':0}}]},
                'selection_counts':{'exact_episode_route':1},'unresolved':[]}

    def test_changed_body_and_unchanged_user_are_distinct_evidence(self):
        before=self.snapshot();after=copy.deepcopy(before)
        after['episodes']=(b'new',)+after['episodes']
        after['rows'][1]['bodies'][102]='changed'
        after['rows'][1]['modification']=1
        report=compare(before,after)
        self.assertEqual(report['transition_counts'],{'body_channels=102;modification=increased;user=same':1})
        self.assertTrue(report['old_episode_mapping_is_suffix'])
        self.assertFalse(report['autodesk_save_rule_inferred'])

    def test_reused_ids_and_unresolved_records_not_counted_as_body_changes(self):
        before=self.snapshot();after=copy.deepcopy(before)
        after['rows'][1]['unique_id']='different'
        report=compare(before,after)
        self.assertEqual(report['shared_ids_with_changed_native_unique_id'],[1])
        self.assertEqual(report['transition_counts'],{})
        after['rows'][1]['unique_id']='id';after['rows'][1]['bodies']=None
        self.assertEqual(compare(before,after)['shared_ids_with_unresolved_body_selection'],[1])

    def test_sentinel_transition_and_added_removed(self):
        before=self.snapshot();after=copy.deepcopy(before)
        before['rows'][1]['user_modification']=0xffffffff
        after['rows'][2]=copy.deepcopy(after['rows'][1]);before['rows'][3]=copy.deepcopy(before['rows'][1])
        report=compare(before,after)
        self.assertEqual(report['added_project_ids'],[2]);self.assertEqual(report['removed_project_ids'],[3])
        self.assertEqual(report['transition_counts'],{'body_channels=unchanged;modification=same;user=sentinel_to_episode':1})

    def test_unrelated_or_reordered_episode_lineage_rejected(self):
        before=self.snapshot();after=copy.deepcopy(before)
        after['episodes']=(b'unrelated',)
        with self.assertRaisesRegex(ValueError, 'episode lineage'):compare(before,after)
