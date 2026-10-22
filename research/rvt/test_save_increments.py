import copy
import struct
import unittest
from save_increments import decode, encode, REVISIONS


class IncrementCodecTests(unittest.TestCase):
    def fixture(self):
        row = {'m_incrementVersions': [{'m_causedByIncrementNumber': -1, 'm_totalElements': 7}],
               'm_userName': 'A😀', 'm_comment': '', 'm_greatest': {'m_id': 3},
               'm_totalEpisodes': 4, 'm_atimeStamp': {'m_msb': 0, 'm_lsb': 0xffffffff},
               'm_majorVersion': 1, 'm_totalElements': 7, 'm_overwrite': False}
        row.update((f'm_{n}StreamRevision', -1) for n in REVISIONS)
        return {'m_increments': [row], 'm_localIncrements': [copy.deepcopy(row)], 'm_permutation': []}

    def test_profiles_unicode_and_independent_arrays(self):
        for tag in (1248, 1283, 1313):
            fields = self.fixture()
            fields['m_localIncrements'][0]['m_comment'] = 'separate\0value'
            raw = encode(tag, fields)
            self.assertEqual(decode(raw), (tag, fields))
            self.assertEqual(encode(*decode(raw)), raw)

    def test_every_truncation_and_extra_bytes_rejected(self):
        raw = encode(1283, self.fixture())
        for size in range(len(raw)):
            with self.assertRaises(ValueError): decode(raw[:size])
        for bad in (raw+b'\0', raw[:-1]+b'\1', b'\0\0'+raw[2:], raw[:2]+b'\xff'*4+raw[6:]):
            with self.assertRaises(ValueError): decode(bad)

    def test_nonempty_permutation_rejected_without_guessing_wire_layout(self):
        fields = self.fixture()
        fields['m_permutation'] = [{'first': {'m_id': 0}, 'second': 1}]
        with self.assertRaisesRegex(ValueError, 'nonempty increment permutation'):
            encode(1283, fields)
        fields['m_permutation'] = []
        raw = encode(1283, fields)
        # The count is immediately before the four-byte closing marker.
        raw = raw[:-8]+struct.pack('<I', 1)+struct.pack('<ii', 0, 1)+raw[-4:]
        with self.assertRaisesRegex(ValueError, 'nonempty increment permutation'):
            decode(raw)

    def test_revisions_can_be_changed_without_losing_fields(self):
        fields = self.fixture(); before = encode(1283, fields)
        fields['m_increments'][0]['m_historyStreamRevision'] = 8
        after = encode(1283, fields)
        self.assertEqual(len(before), len(after))
        self.assertEqual(sum(a != b for a, b in zip(before, after)), 4)
        self.assertEqual(decode(after)[1], fields)

    def test_invalid_flags_unknown_fields_and_range_rejected(self):
        for field, value in [('m_overwrite', 2), ('m_totalEpisodes', 2**31), ('unknown', 0)]:
            fields = self.fixture(); fields['m_increments'][0][field] = value
            with self.assertRaises(ValueError): encode(1283, fields)
        raw = bytearray(encode(1283, self.fixture()))
        # First array has one version, two strings, then 18 i32 fields and bool.
        first_flag = 6+12+10+4+72
        self.assertEqual(raw[first_flag], 0)
        raw[first_flag] = 2
        with self.assertRaises(ValueError): decode(raw)
