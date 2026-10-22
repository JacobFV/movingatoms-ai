import copy
import unittest
from verify_bookkeeping import reconcile

class BookkeepingTests(unittest.TestCase):
    def fixture(self):
        b={'sha256':'fixture','file':'fixture.rvt','reader_commit':'test','episode_count':2,
           'history_root':{'fields':{'m_nextLocalSequenceNumber':2},'field_spans':[]},
           'increment_root':{'fields':{}},'modification_episode_histogram':{'0':1},
           'increments':[{'stored_elements':3,'greatest_episode':1,'total_episodes':2}],
           'table_record_count':1,'partition_id_histogram':{'0':1},'graveyard_records':0,'room_identity':None}
        o={'sha256':'fixture','streams':[{'stream':'Partitions/0',
             'segments':[{'declared_count':1},{'declared_count':2}]}]}
        return b,o

    def test_count_includes_embedded_groups(self):
        b,o=self.fixture();r=reconcile([b],[o])[0]
        self.assertEqual(r['streams'][0]['all_group_objects'],3)
        self.assertEqual(r['streams'][0]['base_objects'],1)

    def test_stale_count_missing_stream_and_history_fail(self):
        b,o=self.fixture()
        for mutation in ('count','missing','history','hash'):
            bad=copy.deepcopy(b);obj=copy.deepcopy(o)
            if mutation=='count':bad['increments'][0]['stored_elements']=1
            if mutation=='missing':obj['streams']=[]
            if mutation=='history':bad['modification_episode_histogram']={'2':1}
            if mutation=='hash':obj['sha256']='other'
            with self.assertRaises(ValueError):reconcile([bad],[obj])
