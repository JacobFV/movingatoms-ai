import unittest
from dataclasses import replace
from partition_objects import Record,validate
from partition_segments import Segment
from object_writer import pack_records,replace_records
from test_partition_objects import fixture
from test_data_objects import object_bytes,PARAMETER
from data_objects import replace_record_text


class ObjectWriterTests(unittest.TestCase):
    def test_boundary_sizes_both_profiles_and_all_sequences(self):
        for width in (4,8):
            for size in range(0,260):
                items=[Record(1,bytes(range(256))[:size] if size<=256 else b'x'*size),
                       Record(2,b'next'),Record((1<<(width*8))-1,b'')]
                members=tuple(m for seq in (101,102,103) for m in pack_records(items,seq,width,32))
                result=validate(Segment(2,None,members,b'',b''),width)
                self.assertTrue(all(v==items for v in result.values()))
                self.assertTrue(all(len(m.inflate())<=32 for m in members))

    def test_edit_guards_and_preservation(self):
        segment=fixture(8);old=validate(segment,8)[102][0];new=replace(old,body=b'new'*100)
        result=replace_records(segment,8,{(102,old.element_id):(old,new)},32)
        for seq in (101,103):
            self.assertEqual([m for m in segment.members if m.sequence==seq],
                             [m for m in result.members if m.sequence==seq])
        self.assertEqual(validate(result,8)[102][0],new)
        for edits in ({},{(102,1):(new,old)},{(102,1):(old,old)},
                      {(102,1):(old,Record(2,b'bad'))}):
            with self.assertRaises(ValueError):replace_records(segment,8,edits)

    def test_resized_parameter_lengths_include_utf16_surrogates(self):
        old=Record(348738,object_bytes()[16:-4])
        for value in ('Concrete polished','','Cork 🌲'):
            changed=replace_record_text(old,PARAMETER,'Wood',value)
            self.assertEqual(len(changed.body)-len(old.body),len(value.encode('utf-16le'))-8)
            self.assertEqual(replace_record_text(changed,PARAMETER,value,'Wood'),old)
        with self.assertRaises(ValueError):replace_record_text(old,PARAMETER,'Tile','Concrete')
