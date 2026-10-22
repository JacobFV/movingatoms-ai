from dataclasses import replace
import unittest
from save_history import History, decode, encode, prepend_episode


class HistoryCodecTests(unittest.TestCase):
    def fixture(self, tag=1279):
        return History(tag, 1, 0, 2, 0, (bytes(range(16)),)*5,
                       (3, 8, 20), (b'a'*16+b'\x28', b'b'*16+b'\x28'))

    def test_all_profiles_and_variable_upgrade_array(self):
        for tag in (1244, 1279, 1309):
            for upgrades in ((), (3, 8, 20)):
                h = replace(self.fixture(tag), upgrade_versions=upgrades)
                self.assertEqual(decode(encode(h)), h)

    def test_mutation_preserves_existing_reverse_ids(self):
        h = self.fixture(); new = prepend_episode(h, b'c'*16)
        self.assertEqual(new.next_sequence, 3)
        self.assertEqual(new.episodes[1:], h.episodes)
        for episode_id in range(2):
            self.assertEqual(h.episodes[len(h.episodes)-1-episode_id],
                             new.episodes[len(new.episodes)-1-episode_id])
        self.assertEqual(new.guids, h.guids)
        self.assertEqual(new.upgrade_versions, h.upgrade_versions)

    def test_every_truncation_and_unsupported_layout(self):
        raw = encode(self.fixture())
        for n in range(len(raw)):
            with self.assertRaises(ValueError): decode(raw[:n])
        for offset, value in ((0, 0), (2, 2), (10, 1), (102, 255), (len(raw)-5, 0), (len(raw)-1, 1)):
            changed = bytearray(raw); changed[offset] = value
            with self.assertRaises(ValueError): decode(changed)
        with self.assertRaises(ValueError): decode(raw+b'\0')

    def test_mutation_rejects_unsupported_allocation_and_duplicate_guid(self):
        h = self.fixture()
        for bad in (replace(h, next_sequence=9), replace(h, subsequence_deficit=1)):
            self.assertEqual(decode(encode(bad)), bad)
            with self.assertRaises(ValueError): prepend_episode(bad, b'c'*16)
        for guid in (b'a'*16, b'\0'*16, b'short'):
            with self.assertRaises(ValueError): prepend_episode(h, guid)
        with self.assertRaises(ValueError): encode(replace(h, episodes=(b'a',)))
        with self.assertRaises(ValueError): encode(replace(h, next_sequence=2**31))

    def test_schema_signed_fields_preserved_but_not_allocated(self):
        h = replace(self.fixture(), next_sequence=-1, subsequence_deficit=-2,
                    upgrade_versions=(-2147483648, 2147483647))
        self.assertEqual(decode(encode(h)), h)
        with self.assertRaises(ValueError): prepend_episode(h, b'c'*16)
