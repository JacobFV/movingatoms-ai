import random
import unittest
from paged import decode, encode, trailer, MASK
from pages import PAYLOAD, STORED
from bch_probe import polynomial_gcd


def scalar_parity(payload, lane):
    # Independent scalar polynomial division, not the encoder's bit-sliced LFSR.
    value = int.from_bytes(payload, 'little')
    message = 0
    for i in range(2036):
        message = message << 1 | ((value >> (i*255+lane)) & 1)
    remainder = message << 11
    while remainder.bit_length() > 11:
        remainder ^= 0x805 << (remainder.bit_length()-12)
    return remainder


class ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = random.Random(745).randbytes(PAYLOAD)

    def test_independent_scalar_polynomial_division(self):
        parity = int.from_bytes(trailer(self.payload), 'little') >> 12
        for lane in range(255):
            got = 0
            for i in range(11):
                got = got << 1 | ((parity >> (i*255+lane)) & 1)
            self.assertEqual(got, scalar_parity(self.payload, lane))

    def test_boundaries(self):
        for size in (0, 1, PAYLOAD-1, PAYLOAD, PAYLOAD+1, 2*PAYLOAD, 2*PAYLOAD+17):
            with self.subTest(size=size):
                data = (self.payload * 3)[:size]
                stored = encode(data)
                self.assertEqual(len(stored), size + size//PAYLOAD*353)
                self.assertEqual(decode(stored), data)

    def test_corruption_in_data_parity_and_padding(self):
        stored = bytearray(encode(self.payload))
        for pos, bit in ((0, 1), (PAYLOAD-1, 128), (PAYLOAD, 1),
                         (PAYLOAD+1, 1), (PAYLOAD+1, 16),
                         (STORED-1, 1), (STORED-1, 128)):
            with self.subTest(pos=pos, bit=bit):
                bad = stored.copy()
                bad[pos] ^= bit
                with self.assertRaises(ValueError): decode(bad)

    def test_truncation(self):
        stored = encode(self.payload)
        for lost in (1, 100, 353):
            with self.assertRaises(ValueError): decode(stored[:-lost])

    def test_linear(self):
        b = bytes(reversed(self.payload))
        self.assertEqual(trailer(bytes(x ^ y for x, y in zip(self.payload, b))),
                         bytes(x ^ y for x, y in zip(trailer(self.payload), trailer(b))))
        self.assertEqual(trailer(bytes(PAYLOAD)), bytes(353))

    def test_payload_length_rejected(self):
        for data in (b'', self.payload[:-1], self.payload+b'x'):
            with self.assertRaises(ValueError): trailer(data)

    def test_cyclic_generator_recovery(self):
        # Multiplication over GF(2): two coprime messages times generator.
        g = 0x805
        self.assertEqual(polynomial_gcd(g ^ (g << 2), g ^ (g << 1) ^ (g << 2)), g)

if __name__ == '__main__':
    unittest.main()
