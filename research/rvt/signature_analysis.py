"""Reproducible file-only SignatureMarker structure and coverage probes.

No failed digest hypothesis establishes a signature scheme or a secret key.
Only source fixtures should be supplied, never synthetic edited candidates.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

import olefile
from codec import decode as unpage
from partition_segments import decode, PROFILES

ED25519_ORDER = 2**252 + 27742317777372353535851937790883648493
P256_ORDER = int('ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551', 16)


def scalar_structure(value):
    """Necessary shape checks only: never cryptographic verification."""
    if len(value) != 64:
        raise ValueError('expected a 64-byte footer')
    return {
        'ed25519_canonical_s': int.from_bytes(value[32:], 'little') < ED25519_ORDER,
        'p256_raw_big_endian_rs_range': all(0 < int.from_bytes(value[i:i+32], 'big') < P256_ORDER for i in (0, 32)),
        'p256_raw_big_endian_low_s': 0 < int.from_bytes(value[32:], 'big') <= P256_ORDER // 2,
        'identical_halves': value[:32] == value[32:],
    }


def coverage_candidates(segment, root):
    chunks = [m.inflate() for m in segment.members]
    sequences = sorted({m.sequence for m in segment.members})
    values = {'inflated': b''.join(chunks),
              'gzip': b''.join(m.compressed for m in segment.members)}
    tag = PROFILES[root][0]
    values['member_blocks'] = b''.join(
        struct.pack('<HIIIIQ', tag, m.kind, m.count, len(m.compressed)+8, m.body_length, m.sequence)
        + m.compressed + struct.pack('<HI', tag-7, len(m.compressed)+8)
        for m in segment.members)
    for seq in sequences:
        values[f'inflated_sequence_{seq}'] = b''.join(data for m, data in zip(segment.members, chunks) if m.sequence == seq)
    # Scope is deliberately enumerated; not an exhaustive coverage search.
    base = list(values.items())
    context = struct.pack('<I', segment.count) + (segment.guid or b'')
    for name, data in base:
        values[f'count_guid_then_{name}'] = context + data
        values[f'{name}_then_count_guid'] = data + context
    return values


def analyze(paths):
    files = []; signatures = defaultdict(list); inputs = defaultdict(list)
    structure = Counter(); matches = []; empty = []; tested = 0
    algorithms = ('sha512', 'sha3_512', 'blake2b')
    for path in paths:
        count = 0
        with olefile.OleFileIO(path) as f:
            for parts in f.listdir():
                if parts[0] != 'Partitions': continue
                p = decode(unpage(f.openstream(parts).read()))
                for index, segment in enumerate(p.segments):
                    count += 1
                    location = {'file': path.name, 'stream': '/'.join(parts), 'segment': index,
                                'count': segment.count, 'content_key': segment.guid.hex() if segment.guid else None}
                    if not segment.footer:
                        empty.append({**location, 'members': len(segment.members),
                                      'inflated_bytes': sum(len(m.inflate()) for m in segment.members),
                                      'public_signature_empty': not segment.label})
                        continue
                    signatures[segment.footer.hex()].append(location)
                    structure.update({key: int(value) for key, value in scalar_structure(segment.footer).items()})
                    candidates = coverage_candidates(segment, p.root_tag)
                    inputs[hashlib.sha256(candidates['inflated']).hexdigest()].append(
                        {**location, 'footer': segment.footer.hex()})
                    for coverage, data in candidates.items():
                        for algorithm in algorithms:
                            digest = hashlib.new(algorithm, data).digest()
                            for order, expected in [('forward', digest), ('reversed', digest[::-1])]:
                                tested += 1
                                if expected == segment.footer:
                                    matches.append({**location, 'algorithm': algorithm, 'coverage': coverage, 'order': order})
        files.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'groups': count})
    values = [bytes.fromhex(value) for value, locations in signatures.items() for _ in locations]
    n = len(values)
    return {'files': files, 'nonempty_private_signature_groups': n, 'empty_field_groups': empty,
            'structure_true_counts': dict(structure),
            'constant_byte_positions': [i for i in range(64) if n and len({v[i] for v in values}) == 1],
            'byte_position_distinct_counts': [len({v[i] for v in values}) for i in range(64)],
            'duplicate_footer_groups': [v for v in signatures.values() if len(v) > 1],
            'duplicate_inflated_groups': [v for v in inputs.values() if len(v) > 1],
            'digest_algorithms': algorithms, 'digest_comparisons': tested, 'digest_matches': matches,
            'limits': ['Scalar range checks are necessary shape tests, not verification.',
                       'Ed25519 exclusion applies only to standard raw R||S with canonical little-endian S.',
                       'P-256 raw scalar ranges admit almost all random 64-byte strings.',
                       'Nonmatches reject only the enumerated digest and coverage combinations.',
                       'No claim about keys, enforcement, acceptance, or proprietary implementation.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    print(json.dumps(analyze(parser.parse_args().files), indent=2))
