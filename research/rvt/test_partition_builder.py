import unittest
from partition_builder import build_partition
from partition_objects import Record,validate
from partition_segments import encode,decode

class PartitionBuilderTests(unittest.TestCase):
    def test_empty_groups_all_profiles(self):
        for root,width in ((0x365,4),(0x37b,8),(0x391,8)):
            for trailing in (False,True):
                p=build_partition(root,{s:[] for s in (101,102,103)},width,trailing)
                self.assertEqual(p,decode(encode(p)))
                self.assertEqual(p.segments[0].count,0)
                self.assertTrue(all(len(v)==1 for v in validate(p.segments[0],width).values()))

    def test_nonempty_opt_in_split_objects_and_original_lists(self):
        groups={s:[Record(9,b'x'*500),Record(3,b'second')] for s in (101,102,103)}
        with self.assertRaisesRegex(ValueError,'opt-in'):build_partition(0x391,groups,8)
        p=build_partition(0x391,groups,8,allow_unsigned_nonempty=True,member_limit=32)
        result=validate(p.segments[0],8)
        for seq in groups:self.assertEqual(result[seq][:-1],groups[seq])
        self.assertEqual(p.segments[0].count,2)
        self.assertEqual(p.segments[0].footer,b'')
        self.assertTrue(any(m.kind==7 for m in p.segments[0].members))
        self.assertTrue(all(len(v)==2 for v in groups.values()))

    def test_bad_profiles_ids_and_sequence_sets_rejected(self):
        good={s:[Record(1,b'body')] for s in (101,102,103)}
        for root,width in ((0x391,4),(0x365,8),(0,8)):
            with self.assertRaises(ValueError):build_partition(root,good,width,allow_unsigned_nonempty=True)
        for bad in ({101:[]}, {101:good[101],102:[],103:good[103]},
                    {s:[Record(1,b'a'),Record(1,b'b')] for s in good},
                    {s:[Record((1<<64)-1,b'')] for s in good}):
            with self.assertRaises(ValueError):build_partition(0x391,bad,8,allow_unsigned_nonempty=True)
