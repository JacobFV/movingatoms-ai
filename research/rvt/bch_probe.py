"""Find shared binary cyclic-code factors, without guessing a field polynomial.

For a systematic binary BCH/CRC code every codeword polynomial is divisible
by its generator. GCD across independent pages therefore contains that generator.
We test explicit lane layouts, MSB/LSB bit order, payload/parity reversals, and
parity-before/after-payload. Failure excludes these layouts, not ECC generally.
"""
import argparse
import json
import math
from pathlib import Path
from pages import PAYLOAD, STORED

REVERSE = bytes(int(f'{x:08b}'[::-1], 2) for x in range(256))


def polynomial_gcd(a, b):
    while b:
        if a.bit_length() < b.bit_length():
            a, b = b, a
        a ^= b << (a.bit_length() - b.bit_length())
    return a


def lanes(page, count, layout, parity_layout):
    data, parity = page[:PAYLOAD], page[PAYLOAD + 1:]
    if len(page) != STORED or len(data) % count or len(parity) % count:
        raise ValueError('layout must split payload and parity into equal lanes')
    for i in range(count):
        d = data[i::count] if layout == 'striped' else data[i*len(data)//count:(i+1)*len(data)//count]
        p = parity[i::count] if parity_layout == 'striped' else parity[i*len(parity)//count:(i+1)*len(parity)//count]
        yield d, p


def probe(pages):
    results = []
    # Equal lanes dividing both 64896 and 352. All lanes of the first pages
    # are checked for positive candidates; two independent pages reject fast.
    for count in (1, 2, 4, 8, 16, 32):
        for layout in ('contiguous', 'striped'):
            for parity_layout in ('contiguous', 'striped'):
                if count == 1 and (layout != 'contiguous' or parity_layout != 'contiguous'):
                    continue
                pairs = [list(lanes(p, count, layout, parity_layout)) for p in pages]
                for rd in (False, True):
                    for rp in (False, True):
                        for before in (False, True):
                            for bits in ('msb', 'lsb'):
                                g = 0
                                checked = 0
                                for page in pairs:
                                    d, p = page[0]
                                    if rd: d = d[::-1]
                                    if rp: p = p[::-1]
                                    word = p + d if before else d + p
                                    if bits == 'lsb': word = word.translate(REVERSE)
                                    g = polynomial_gcd(g, int.from_bytes(word, 'big'))
                                    checked += 1
                                    if g.bit_length() <= 33:
                                        break
                                degree = g.bit_length() - 1
                                results.append({'lanes': count, 'payload_layout': layout,
                                    'parity_layout': parity_layout, 'reverse_payload': rd,
                                    'reverse_parity': rp, 'parity_first': before,
                                    'bit_order': bits, 'gcd_degree': degree,
                                    'pages_checked': checked,
                                    'parity_bits_per_lane': 352*8//count})
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pages', type=Path)
    args = parser.parse_args()
    raw = args.pages.read_bytes()
    if len(raw) % STORED: parser.error('incomplete page export')
    # Widely spaced pages avoid correlated neighbouring data.
    pages = [raw[i*STORED:(i+1)*STORED] for i in (0, len(raw)//STORED//2, len(raw)//STORED-1)]
    results = probe(pages)
    print(json.dumps({'hypotheses': len(results), 'results': results}, indent=2))
