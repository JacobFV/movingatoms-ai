import random
import unittest
from codec import decode, encode, decode_final, encode_final, choose, padded_data, Layout, encode_final_with_layout
from pages import PAYLOAD
from partial_pages import parity

class CompleteCodecTests(unittest.TestCase):
    def test_sizes_and_arbitrary_last_bits(self):
        rng = random.Random(548)
        for size in list(range(1,130)) + [182,294,774,1890,4096,16000,42093,64895,PAYLOAD,PAYLOAD+1,2*PAYLOAD]:
            for data in (rng.randbytes(size), bytes(size)):
                with self.subTest(size=size, zero=not any(data)):
                    self.assertEqual(decode(encode(data)), data)
        self.assertEqual(encode(b''), b'')
        self.assertEqual(decode(b''), b'')

    def test_valid_parity_cannot_hide_invalid_padding_footer(self):
        data = random.Random(1).randbytes(774)
        layout = choose(data)
        value = padded_data(data, layout)
        start = layout.data_bits-layout.footer_bits
        value ^= 1 << start  # padding count is no longer divisible by eight
        full = value | parity(value,layout.lanes,layout.words-layout.degree,layout.generator)<<layout.data_bits
        bad = full.to_bytes(layout.size,'little')
        with self.assertRaises(ValueError): decode_final(bad)

    def test_truncated_and_corrupted_final_page(self):
        raw = encode_final(random.Random(2).randbytes(1000))
        for bad in [raw[:-1], raw[:-4], bytes([raw[0]^1])+raw[1:]]:
            with self.assertRaises(ValueError): decode_final(bad)

    def test_historical_noncanonical_layouts(self):
        rng = random.Random(824)
        for size, layout in [(308, Layout(65,44,0x43)), (739, Layout(65,98,0x83)),
                             (1697, Layout(65,218,0x211)),
                             (4136, Layout(67,511,0x211))]:
            data = rng.randbytes(size-1)+b'\0'
            self.assertNotEqual(choose(data), layout)
            stored = encode_final_with_layout(data, layout)
            self.assertEqual(decode_final(stored), data)
            self.assertEqual(encode_final_with_layout(decode_final(stored), layout), stored)
            corrupt = bytearray(stored); corrupt[0] ^= 1
            with self.assertRaises(ValueError): decode_final(corrupt)
