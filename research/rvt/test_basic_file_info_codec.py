import struct
import unittest
from basic_file_info_codec import decode, encode, wide, COUNTERS, GUIDS

GUID = '49409459-71bb-4a7f-9f74-674b7dd20d9d'
NEXT = '01234567-89ab-4cde-8f01-23456789abcd'


def fixture(count=99):
    prefix = (struct.pack('<I', 14)+b'opaque-header'+struct.pack('<I', count)
              +wide(GUID)+wide(GUID)+wide(str(count))
              +wide('00000000-0000-0000-0000-000000000000')+b'opaque-tail\r\n')
    text = 'Worksharing: Not enabled\r\n'
    text += ''.join(key+': '+str(count)+'\r\n' for key in COUNTERS)
    text += ''.join(key+': '+GUID+'\r\n' for key in GUIDS)
    return prefix+text.encode('utf-16-le')+b'opaque-end'


class BasicFileInfoCodecTests(unittest.TestCase):
    def test_resize_all_counter_copies_and_guids(self):
        data = fixture()
        source = decode(data)
        self.assertEqual(encode(source), data)
        changed = encode(source, 100, NEXT)
        result = decode(changed)
        self.assertEqual((result.increments, result.guid), (100, NEXT))
        self.assertEqual(len(changed)-len(data), 6)
        self.assertEqual(result.text_start-source.text_start, 2)
        self.assertEqual(encode(result, 99, GUID), data)
        self.assertEqual(changed.count(NEXT.encode('utf-16-le')), 4)
        self.assertNotIn(GUID.encode('utf-16-le'), changed)
        for marker in (b'opaque-header', b'opaque-tail\r\n', b'opaque-end'):
            self.assertEqual(changed.count(marker), 1)

    def test_counter_binary_text_mismatch_rejected(self):
        data = bytearray(fixture()); identity = decode(bytes(data))
        struct.pack_into('<I', data, identity.binary_counter, 98)
        with self.assertRaisesRegex(ValueError, 'binary counter disagrees'):
            decode(bytes(data))
        data = bytearray(fixture())
        start, end = identity.binary_counter_string
        data[start:end] = wide('98')
        with self.assertRaisesRegex(ValueError, 'binary decimal counter disagrees'):
            decode(bytes(data))

    def test_unknown_or_ambiguous_layout_rejected(self):
        data = fixture(); identity = decode(data)
        with self.assertRaisesRegex(ValueError, 'unsupported BasicFileInfo header'):
            decode(struct.pack('<I', 15)+data[4:])
        first = identity.binary_guid_spans[0][0]
        with self.assertRaisesRegex(ValueError, 'GUID pair framing'):
            decode(data[:first]+b'gap'+data[first:identity.binary_guid_spans[1][0]]+b'gap'+data[identity.binary_guid_spans[1][0]:])
        with self.assertRaisesRegex(ValueError, 'ambiguous identity property'):
            decode(data+(COUNTERS[0]+': 99\r\n').encode('utf-16-le'))

    def test_invalid_edits_and_spans_rejected(self):
        identity = decode(fixture())
        for count in (-1, True, 2**31):
            with self.assertRaises(ValueError):
                encode(identity, count)
        with self.assertRaisesRegex(ValueError, 'invalid document GUID'):
            encode(identity, document_guid='invalid')
        identity.text_spans[COUNTERS[0]] = (0, 1)
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            encode(identity, 100)

    def test_shrink_and_zero(self):
        source = decode(fixture(1000))
        for count in (99, 9, 0):
            result = decode(encode(source, count))
            self.assertEqual(result.increments, count)
            self.assertEqual(encode(result, 1000), source.source)
