"""Boundary tests for negative signature-shape evidence."""
import unittest
from signature_analysis import ED25519_ORDER, P256_ORDER, scalar_structure


class SignatureShapeTests(unittest.TestCase):
    def test_ed25519_boundary_and_byte_order(self):
        self.assertTrue(scalar_structure(b'\xff'*32 + (ED25519_ORDER-1).to_bytes(32, 'little'))['ed25519_canonical_s'])
        self.assertFalse(scalar_structure(b'\x00'*32 + ED25519_ORDER.to_bytes(32, 'little'))['ed25519_canonical_s'])
        self.assertFalse(scalar_structure(b'\x00'*32 + b'\x00'*31 + b'\x80')['ed25519_canonical_s'])

    def test_p256_ranges_are_not_verification(self):
        r = (1).to_bytes(32, 'big')
        self.assertTrue(scalar_structure(r+r)['p256_raw_big_endian_rs_range'])
        self.assertFalse(scalar_structure(r+b'\x00'*32)['p256_raw_big_endian_rs_range'])
        self.assertFalse(scalar_structure(r+P256_ORDER.to_bytes(32, 'big'))['p256_raw_big_endian_rs_range'])
        self.assertTrue(scalar_structure(r+(P256_ORDER//2).to_bytes(32, 'big'))['p256_raw_big_endian_low_s'])
        self.assertFalse(scalar_structure(r+(P256_ORDER//2+1).to_bytes(32, 'big'))['p256_raw_big_endian_low_s'])

    def test_exact_width(self):
        for size in (0, 32, 63, 65):
            with self.assertRaises(ValueError): scalar_structure(b'\x00'*size)


if __name__ == '__main__': unittest.main()
