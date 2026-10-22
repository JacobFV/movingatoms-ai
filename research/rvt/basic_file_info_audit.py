"""Audit complete known identity copies and variable-length BasicFileInfo edits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
import zlib
import olefile
from schema_probe import REV
from fetch_fixture import FILES, HOLDOUTS
from basic_file_info_codec import decode, encode
from codec import decode as unpage
from save_history import decode as history_decode, GUID_NAMES


def audit(source, directory, target):
    source = source.resolve()
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'], check=True)
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        project = Path(tmp); (project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_name('basic_file_info_probe.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-basic-file-info-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo', 'build', '--release', '--offline', '--manifest-path', str(project/'Cargo.toml'), '--target-dir', str(target.resolve())], check=True)
        reports = []
        for name, expected in [(n, h) for _, n, h in FILES]+HOLDOUTS:
            path = directory/name
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if sha != expected:
                raise ValueError('fixture hash mismatch')
            with olefile.OleFileIO(path) as file:
                data = file.openstream('BasicFileInfo').read()
                history = history_decode(zlib.decompress(unpage(file.openstream('Global/History').read())[8:], 31))
            identity = decode(data)
            if encode(identity) != data:
                raise ValueError('identity roundtrip differs')
            (project/'original').write_bytes(data)
            trials = []
            for count in (99, 100, 1000, 9):
                guid = '01234567-89ab-4cde-8f01-23456789abcd'
                changed = encode(identity, count, guid)
                decoded = decode(changed)
                if encode(decoded, identity.increments, identity.guid) != data:
                    raise ValueError('reverse edit fails exact reconstruction')
                (project/'changed').write_bytes(changed)
                independent = json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-basic-file-info-probe'), str(project/'original'), str(project/'changed'), str(count), guid]))
                trials.append({'count': count, 'stored_bytes': len(changed),
                    'byte_length_delta': len(changed)-len(data),
                    'reverse_edit_byte_exact': True, **independent})
            model_offset = identity.binary_counter_string[1]
            model_guid = uuid.UUID(data[model_offset+4:model_offset+76].decode('utf-16-le'))
            model_matches = [field for field, value in zip(GUID_NAMES, history.guids) if value == model_guid.bytes_le]
            reports.append({'file': name, 'sha256': sha, 'reader_commit': REV,
                'basic_file_info_bytes': len(data),
                'basic_file_info_sha256': hashlib.sha256(data).hexdigest(),
                'text_start': identity.text_start, 'increments': identity.increments,
                'document_guid': identity.guid,
                'following_model_identity_guid': str(model_guid),
                'following_model_identity_nonzero': model_guid.int != 0,
                'following_model_identity_history_matches': model_matches,
                'zero_guid_equality_establishes_namespace': False,
                'binary_uint32_counter_offset': identity.binary_counter,
                'binary_guid_record_spans': identity.binary_guid_spans,
                'binary_decimal_record_span': identity.binary_counter_string,
                'text_property_spans': identity.text_spans,
                'byte_exact_roundtrip': True, 'trials': trials})
        return {'status': 'guarded_observed_identity_framing',
                'limitations': ['Opaque prefix fields remain unparsed.',
                    'Observed header value 14 layout only; other arrangements are rejected.',
                    'Independent public reader verifies text properties, not all binary semantics.',
                    'No Autodesk acceptance result.'], 'fixtures': reports}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source', type=Path, required=True)
    p.add_argument('--target', type=Path, required=True)
    p.add_argument('directory', type=Path)
    a = p.parse_args()
    print(json.dumps(audit(a.reader_source, a.directory, a.target), indent=2))
