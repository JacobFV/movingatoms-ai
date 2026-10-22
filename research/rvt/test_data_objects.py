import gzip
import struct
import unittest
import zlib
from data_objects import verify,replace_text
from parameter_experiment import replace_member_payloads
from partition_segments import Member,Segment

PARAMETER=-1006903

def object_bytes():
    content=b'prefix'+struct.pack('<qI',PARAMETER,4)+'Wood'.encode('utf-16le')+b'tail'
    size=len(content)+4;cls=123
    checksum=zlib.adler32(struct.pack('<I',cls)+content)
    return struct.pack('<IIIII',348738,0,checksum,size,cls)+content+struct.pack('<I',size)

class DataObjectTests(unittest.TestCase):
    def test_change_is_bounded_and_checksum_is_recomputed(self):
        raw=object_bytes();data=b'prefix'+raw+b'suffix'
        new,report=replace_text(data,348738,PARAMETER,'Wood','Cork')
        self.assertEqual(verify(data,6),verify(new,6))
        allowed=set(range(report['value_start'],report['value_end']))|set(range(14,18))
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(data,new)) if a!=b))
        self.assertEqual(new[:6],b'prefix');self.assertTrue(new.endswith(b'suffix'))
        self.assertNotEqual(raw[8:12],new[14:18])

    def test_preconditions_duplicates_and_corruption(self):
        raw=object_bytes()
        for data,element,old,new in [(raw,1,'Wood','Cork'),(raw,348738,'Tile','Cork'),
                                     (raw,348738,'Wood','Concrete'),(raw,348738,'Wood','Wood'),
                                     (raw+raw,348738,'Wood','Cork')]:
            with self.assertRaises(ValueError):replace_text(data,element,PARAMETER,old,new)
        for at in (4,8,12,16,25,len(raw)-1):
            bad=bytearray(raw);bad[at]^=1
            self.assertIsNone(verify(bad,0))
            with self.assertRaises(ValueError):replace_text(bytes(bad),348738,PARAMETER,'Wood','Cork')

    def test_object_edit_across_compression_boundaries(self):
        raw=object_bytes();changed,_=replace_text(raw,348738,PARAMETER,'Wood','Cork')
        chunks=[raw[:10],raw[10:35],raw[35:],b'unchanged member']
        members=tuple(Member(4,1,len(c),101,gzip.compress(c,mtime=0))for c in chunks)
        segment=Segment(1,None,members,b'',b'')
        result,indices=replace_member_payloads(segment,raw+chunks[-1],changed+chunks[-1])
        self.assertEqual(indices,[0,1,2])
        self.assertEqual(result.members[-1],members[-1])
        self.assertEqual(b''.join(m.inflate()for m in result.members),changed+chunks[-1])
        self.assertEqual([len(m.inflate())for m in result.members],list(map(len,chunks)))
