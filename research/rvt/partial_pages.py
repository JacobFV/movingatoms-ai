"""Identify shortened final-page Hamming layouts from public fixture bytes.

This is a verifier/research probe. It does not decide how Revit chooses a
canonical layout for a newly sized stream or where meaningful gzip data ends.
"""
import argparse
import json
from pathlib import Path
import olefile
from pages import GLOBAL, STORED

GENERATORS = (0x13, 0x25, 0x43, 0x83, 0x211, 0x805)


def parity(data, lanes, data_words, generator):
    degree = generator.bit_length()-1
    mask = (1 << lanes)-1
    state = [0]*degree
    taps = [i for i in range(degree) if generator >> i & 1]
    for _ in range(data_words):
        feedback = (data & mask) ^ state[-1]
        data >>= lanes
        state = [0]+state[:-1]
        for tap in taps: state[tap] ^= feedback
    result = 0
    for word in state: result = (result << lanes) | word
    return result


def identify(raw):
    value = int.from_bytes(raw, 'little')
    hits = []
    for padding in range(8):
        bits = len(raw)*8-padding
        if value >> bits: continue
        for lanes in range(65, 256):
            if bits % lanes: continue
            words = bits//lanes
            if words > 2047: continue
            for gen in GENERATORS:
                degree = gen.bit_length()-1
                if not degree < words <= (1 << degree)-1: continue
                data_bits = (words-degree)*lanes
                data = value & ((1 << data_bits)-1)
                if parity(data, lanes, words-degree, gen) == value >> data_bits:
                    hits.append({'lanes': lanes, 'codeword_bits': words,
                                 'data_bits': data_bits, 'generator': hex(gen),
                                 'trailing_padding_bits': padding})
    return hits


def probe(path):
    results = []
    with olefile.OleFileIO(path) as f:
        for parts in f.listdir():
            if not (len(parts) == 2 and (parts[0] == 'Partitions' or
                    parts[0] == 'Global' and parts[1] in GLOBAL or parts == ['Formats','Latest'])):
                continue
            raw = f.openstream(parts).read()
            tail = raw[len(raw)//STORED*STORED:]
            results.append({'stream': '/'.join(parts), 'stored_remainder_bytes': len(tail),
                            'layouts': identify(tail) if tail else []})
    return {'file': path.name, 'streams': results}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('files', type=Path, nargs='+')
    args = p.parse_args()
    print(json.dumps([probe(path) for path in args.files], indent=2))
