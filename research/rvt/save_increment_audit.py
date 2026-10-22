"""Verify the increment codec against independently decoded embedded schema fields."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib
import olefile
from codec import decode as unpage
from save_increments import decode, encode
from schema_probe import REV


def audit(evidence, directory):
    reports = []
    for item in evidence:
        path = directory/item['file']
        if path.parent.resolve() != directory.resolve(): raise ValueError('invalid evidence filename')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256'] or item['reader_commit'] != REV:
            raise ValueError('fixture or reader evidence mismatch')
        with olefile.OleFileIO(path) as source:
            logical = unpage(source.openstream('Global/DocumentIncrementTable').read())
        gzip = zlib.decompressobj(31); data = gzip.decompress(logical[8:])
        if not gzip.eof or gzip.unconsumed_tail: raise ValueError('invalid gzip member')
        tag, fields = decode(data)
        if tag != item['increment_root']['class_tag'] or fields != item['increment_root']['fields']:
            raise ValueError('independent schema decoder disagrees')
        if encode(tag, fields) != data: raise ValueError('increment bytes do not reproduce')
        reports.append({'file': path.name, 'sha256': digest, 'reader_commit': REV,
                        'inflated_bytes': len(data), 'inflated_sha256': hashlib.sha256(data).hexdigest(),
                        'root_tag': tag, 'increments': len(fields['m_increments']),
                        'local_increments': len(fields['m_localIncrements']),
                        'arrays_equal': fields['m_increments'] == fields['m_localIncrements'],
                        'permutation_entries': len(fields['m_permutation']),
                        'schema_fields_equal': True, 'byte_exact_roundtrip': True,
                        'opaque_gzip_suffix_bytes_preserved_by_container': len(gzip.unused_data),
                        'save_transaction_semantics': 'not_established'})
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path); parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.evidence.read_bytes()), args.directory), indent=2))
