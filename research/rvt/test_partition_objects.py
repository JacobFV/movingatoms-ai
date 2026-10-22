import gzip
import struct
import unittest
from dataclasses import replace
from partition_objects import Record,encode_record,records,validate
from partition_segments import Member,Segment


def member(kind,count,bodylen,seq,data):
    return Member(kind,count,bodylen,seq,gzip.compress(data,mtime=0))

def fixture(width):
    out=[]
    for seq in (101,102,103):
        small=Record(1,b'small');big=Record(2,bytes(range(123)))
        end=Record((1<<(8*width))-1,b'')
        out.append(member(4,1,len(small.body),seq,encode_record(small,seq,width)))
        wire=encode_record(big,seq,width);head=width+4+(4 if seq!=101 else 0)
        out.append(member(6,1,32,seq,wire[:head+32]))
        pos=head+32
        while len(wire)-4-pos>32:
            out.append(member(7,0,32,seq,wire[pos:pos+32]));pos+=32
        out.append(member(5,0,len(wire)-4-pos,seq,wire[pos:]))
        out.append(member(4,1,0,seq,encode_record(end,seq,width)))
    return Segment(2,None,tuple(out),b'',b'')

class PartitionObjectTests(unittest.TestCase):
    def test_whole_split_objects_and_sentinels_both_id_widths(self):
        for width in (4,8):
            groups=validate(fixture(width),width)
            self.assertEqual(list(groups),[101,102,103])
            for items in groups.values():
                self.assertEqual(items,[Record(1,b'small'),Record(2,bytes(range(123))),Record((1<<(width*8))-1,b'')])

    def test_crc_counts_lengths_and_sequences_fail_closed(self):
        s=fixture(8)
        with self.assertRaises(ValueError):validate(replace(s,count=3),8)
        for i in range(len(s.members)):
            ms=list(s.members);ms[i]=replace(ms[i],count=ms[i].count+1)
            with self.subTest(member=i),self.assertRaises(ValueError):records(replace(s,members=tuple(ms)),8)
        i=next(i for i,m in enumerate(s.members)if m.sequence==102 and m.kind==4)
        ms=list(s.members);raw=bytearray(ms[i].inflate());raw[8]^=1
        ms[i]=replace(ms[i],compressed=gzip.compress(raw,mtime=0))
        with self.assertRaisesRegex(ValueError,'Adler'):records(replace(s,members=tuple(ms)),8)
        with self.assertRaises(ValueError):records(replace(s,members=s.members[2:]),8)
        with self.assertRaises(ValueError):records(replace(s,members=s.members[:2]),8)

    def test_record_encoder_rejects_invalid_ids_and_profiles(self):
        for width,seq,ident in [(3,101,1),(4,100,1),(4,101,-1),(4,102,1<<32)]:
            with self.assertRaises(ValueError):encode_record(Record(ident,b''),seq,width)
