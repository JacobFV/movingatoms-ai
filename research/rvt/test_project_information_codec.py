from datetime import datetime
import hashlib
import io
import struct
import unittest
import zipfile
from project_information_codec import parse, patch_timestamp
from project_information_audit import metadata

STAMP = '2023-08-06T09:44:06Z'
STAMP_SECONDS = int(datetime.fromisoformat(STAMP).timestamp())


def fixture(extra_text=''):
    xml = ('<?xml version="1.0"?><entry xmlns="http://www.w3.org/2005/Atom" '
           'xmlns:p="urn:schemas-autodesk-com:partatom"><updated>'+STAMP+'</updated>'
           '<title>Unchanged</title><p:design-file><p:updated>'+STAMP+'</p:updated>'
           '</p:design-file>'+extra_text+'</entry>').encode()
    output = io.BytesIO()
    info = zipfile.ZipInfo('private-path.xml', (2023, 8, 6, 9, 44, 6))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.comment = b'entry-comment'; info.external_attr = 0x12340000
    info.extra = b'\x0a\x00\x02\x00xy'
    with zipfile.ZipFile(output, 'w') as archive:
        archive.comment = b'archive-comment'; archive.writestr(info, xml, compresslevel=9)
    data = bytearray(output.getvalue()); central = data.index(b'PK\x01\x02')
    struct.pack_into('<H', data, 6, 2); struct.pack_into('<H', data, central+8, 2)
    return bytes(data)


class ProjectInformationTests(unittest.TestCase):
    def test_both_observed_offsets_and_metadata_preservation(self):
        data = fixture(); sha = hashlib.sha256(data).hexdigest()
        for offset in (14400, 36000):
            current = STAMP_SECONDS+offset
            unchanged, _ = patch_timestamp(data, sha, current, current)
            self.assertEqual(unchanged, data)
            changed, evidence = patch_timestamp(data, sha, current, current+60)
            old_xml, _, *_ = parse(data); new_xml, new_stamp, *_ = parse(changed)
            self.assertEqual(new_stamp, '2023-08-06T09:45:06Z')
            self.assertEqual(new_xml, old_xml.replace(STAMP.encode(), new_stamp.encode()))
            self.assertEqual(metadata(changed), metadata(data))
            self.assertEqual(evidence['source_timestamp_offset_seconds'], offset)

    def test_wrong_source_unknown_offset_or_time_rejected(self):
        data = fixture(); sha = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError, 'source changed'):
            patch_timestamp(data, '0'*64, STAMP_SECONDS+14400, STAMP_SECONDS+14460)
        with self.assertRaisesRegex(ValueError, 'unsupported source timestamp offset'):
            patch_timestamp(data, sha, STAMP_SECONDS, STAMP_SECONDS+60)
        for value in (True, -1, 2**32):
            with self.assertRaisesRegex(ValueError, 'unsupported increment timestamp'):
                patch_timestamp(data, sha, STAMP_SECONDS+14400, value)

    def test_ambiguous_timestamp_and_corrupt_zip_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous XML timestamp'):
            parse(fixture('<title>'+STAMP+'</title>'))
        data = bytearray(fixture()); data[14] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC disagree'):
            parse(bytes(data))
        data = bytearray(fixture()); data[6] = 0
        with self.assertRaisesRegex(ValueError, 'compression flags'):
            parse(bytes(data))
        with self.assertRaisesRegex(ValueError, 'directory layout'):
            parse(fixture()+b'junk')
