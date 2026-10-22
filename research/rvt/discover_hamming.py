"""Reproduce the trailer discovery from raw bytes, independently of the encoder."""
import argparse
import json
from pathlib import Path
from pages import STORED, PAYLOAD
from bch_probe import polynomial_gcd


def discover(raw):
    if not raw or len(raw) % STORED:
        raise ValueError('expected one or more complete stored pages')
    pages = [raw[i:i+STORED] for i in range(0, len(raw), STORED)]
    varying = 0
    for page in pages:
        varying |= int.from_bytes(page[PAYLOAD:], 'little')
    zeros = [i for i in range(353*8) if not (varying >> i) & 1]
    # Test the dimensions suggested by the observed 12+7 zero padding bits:
    # 255 lanes * (2036 data + 11 parity) = 521985 bits.
    g = 0
    witnesses = []
    for page_index, page in enumerate(pages[:3]):
        value = int.from_bytes(page, 'little')
        for lane in range(8):
            word = sum(((value >> (i*255+lane)) & 1) << i for i in range(2047))
            g = polynomial_gcd(g, word)
            witnesses.append({'page': page_index, 'lane': lane, 'gcd_degree': g.bit_length()-1})
    degree = g.bit_length()-1
    reciprocal = sum(((g >> i) & 1) << (degree-i) for i in range(degree+1))
    return {'pages_observed': len(pages), 'always_zero_trailer_bits_lsb_first': zeros,
            'lane_polynomial_gcd': hex(g), 'reciprocal_generator': hex(reciprocal),
            'witnesses': witnesses}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pages', type=Path)
    args = parser.parse_args()
    print(json.dumps(discover(args.pages.read_bytes()), indent=2))
