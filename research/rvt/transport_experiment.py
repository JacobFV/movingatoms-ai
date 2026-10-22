"""Create hash-guarded native writer experiments; never claims semantic editing.

identity: every eligible stored stream must reproduce byte-for-byte.
gzip-mtime: change only the ElemTable gzip timestamp; the uncompressed table,
all opaque suffix bytes, stream length, and all later pages stay unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zlib
import olefile
from pages import GLOBAL
from codec import decode


def make(input_path, output_dir, mode):
    output_dir.mkdir(parents=True, exist_ok=False)
    patches = []
    evidence = {'mode': mode, 'semantic_edit': False, 'revit_openability': 'not_tested'}
    with olefile.OleFileIO(input_path) as ole:
        for parts in ole.listdir():
            name = '/'.join(parts)
            if mode == 'identity':
                if not (len(parts) == 2 and (parts[0] == 'Partitions' or
                        parts[0] == 'Global' and parts[1] in GLOBAL or parts == ['Formats', 'Latest'])):
                    continue
            elif name != 'Global/ElemTable':
                continue
            raw = ole.openstream(parts).read()
            logical = decode(raw)
            if mode == 'gzip-mtime':
                if logical[8:12] != b'\x1f\x8b\x08\x00':
                    raise ValueError('not the expected single gzip framing')
                before = zlib.decompressobj(31)
                inflated = before.decompress(logical[8:])
                if not before.eof: raise ValueError('incomplete gzip')
                changed = bytearray(logical)
                old_time = int.from_bytes(changed[12:16], 'little')
                changed[12:16] = (old_time ^ 1).to_bytes(4, 'little')
                logical = bytes(changed)
                after = zlib.decompressobj(31)
                if after.decompress(logical[8:]) != inflated or not after.eof or after.unused_data != before.unused_data:
                    raise ValueError('decompressed table or opaque suffix changed')
                evidence.update({'decompressed_sha256': hashlib.sha256(inflated).hexdigest(),
                    'decompressed_bytes': len(inflated), 'opaque_suffix_bytes_preserved': len(before.unused_data),
                    'mtime_before': old_time, 'mtime_after': old_time ^ 1})
            filename = f'{len(patches):03}.bin'
            (output_dir/filename).write_bytes(logical)
            patches.append({'stream': name, 'expected_stored_sha256': hashlib.sha256(raw).hexdigest(),
                            'new_payload_file': filename})
    if not patches: raise ValueError('no matching streams')
    (output_dir/'manifest.json').write_text(json.dumps({
        'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(), 'patches': patches}, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--mode', choices=['identity', 'gzip-mtime'], required=True)
    args = parser.parse_args()
    make(args.input, args.output_dir, args.mode)
