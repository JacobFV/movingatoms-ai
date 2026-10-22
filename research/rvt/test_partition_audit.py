import gzip
import struct
import unittest
import zlib
from partition_audit import audit

class PartitionAuditTests(unittest.TestCase):
    def sample(self):
        data=b'a member with internal fake gzip magic \x1f\x8b\x08'
        gz=gzip.compress(data,mtime=0)
        prefix=struct.pack('<II',9,0)+bytes(10)
        block=struct.pack('<HIIIIQ',0xe7c,7,0,len(gz)+8,len(data),101)
        tail=struct.pack('<HI',0xe75,len(gz)+8)
        ending=struct.pack('<HIIIIHI',0xe7c,0,0,0,0,0xe8f,64)+bytes(range(64))
        return prefix+block+gz+tail+ending

    def test_explicit_length_and_unresolved_footer(self):
        result=audit(self.sample())
        self.assertEqual(len(result['members']),1)
        self.assertEqual(result['footer_bytes'],64)
        self.assertFalse(result['complete_partition_validation'])
        self.assertEqual(result['digest_matches'],[])

    def test_bad_lengths_crc_and_truncation(self):
        raw=self.sample()
        for i in [28,44,len(raw)-18-6-64-1]:
            bad=bytearray(raw);bad[i]^=1
            with self.assertRaises((ValueError,zlib.error)): audit(bad)
        with self.assertRaises(ValueError): audit(raw[:-1])
