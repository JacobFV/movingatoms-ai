"""Test a shared affine binary map on interleaved bit lanes.

Unlike a whole-page linear fit, many lane observations can overdetermine a
small map. Includes an affine constant, so fixed CRC initializers are allowed.
A successful fit is still only a candidate until held-out pages verify.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from pages import PAYLOAD, STORED


def lane_vectors(data, count, layout):
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    matrix = bits.reshape(-1, count).T if layout == 'striped' else bits.reshape(count, -1)
    return [int.from_bytes(row.tobytes(), 'little') for row in np.packbits(matrix, axis=1)]


def fit(pages, count, data_layout, parity_layout):
    basis = {}
    constraints = 0
    for index, page in enumerate(pages):
        xs = lane_vectors(page[:PAYLOAD], count, data_layout)
        ys = lane_vectors(page[PAYLOAD+1:], count, parity_layout)
        for lane, (x, y) in enumerate(zip(xs, ys)):
            # Constant is a distinct low bit; trailing packed padding harmless.
            x = (x << 1) | 1
            while x:
                pivot = x.bit_length()
                if pivot not in basis:
                    basis[pivot] = (x, y)
                    break
                bx, by = basis[pivot]
                x ^= bx
                y ^= by
            if not x:
                constraints += 1
                if y:
                    return {'verdict': 'rejected', 'rank': len(basis),
                            'constraints': constraints, 'page': index, 'lane': lane}
    return {'verdict': 'consistent' if constraints else 'underdetermined',
            'rank': len(basis), 'constraints': constraints}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pages', type=Path)
    args = parser.parse_args()
    raw = args.pages.read_bytes()
    if len(raw) % STORED: parser.error('incomplete page export')
    pages = [raw[i:i+STORED] for i in range(0, len(raw), STORED)]
    results = []
    for count in (256, 128, 64, 32):
        for dl in ('striped', 'contiguous'):
            for pl in ('striped', 'contiguous'):
                r = {'lanes': count, 'payload_layout': dl, 'parity_layout': pl,
                     **fit(pages, count, dl, pl)}
                results.append(r)
                print(json.dumps(r), flush=True)
