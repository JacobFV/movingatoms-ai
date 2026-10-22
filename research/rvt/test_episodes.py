import struct
import unittest
from episode_experiment import episodes, prepend

class EpisodeTests(unittest.TestCase):
    def sample(self):
        data = bytearray(110)
        struct.pack_into('<I', data, 14, 2)
        struct.pack_into('<I', data, 106, 2)
        return bytes(data)+b'a'*16+b'\x28'+b'b'*16+b'\x28'+b'footer'

    def test_prepend_preserves_number_mapping_and_footer(self):
        data = self.sample()
        changed = prepend(data, b'c'*16)
        entries = episodes(changed)[2]
        self.assertEqual(entries, [b'c'*16+b'\x28', b'a'*16+b'\x28', b'b'*16+b'\x28'])
        self.assertTrue(changed.endswith(b'footer'))
        self.assertEqual(struct.unpack_from('<I', changed, 14)[0], 3)
        self.assertEqual(struct.unpack_from('<I', changed, 106)[0], 3)

    def test_rejects_old_spike_mistakes_and_duplicates(self):
        original = self.sample()
        with self.assertRaises(ValueError): prepend(original, b'a'*16)
        bad = bytearray(original)
        struct.pack_into('<I', bad, 14, 3)
        with self.assertRaises(ValueError): episodes(bad)
        bad = bytearray(original)
        bad[126] = 0x3f
        with self.assertRaises(ValueError): episodes(bad)
