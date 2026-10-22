"""Audit file identity and storage revision fields using file-embedded schemas."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import uuid
import tempfile
import zlib
import olefile
from codec import decode as unpage
from schema_probe import REV
from save_increments import decode as increments_decode
from save_history import decode as history_decode, GUID_NAMES


def inflated(data, offset):
    d = zlib.decompressobj(31)
    raw = d.decompress(data[offset:])
    if not d.eof or d.unconsumed_tail:
        raise ValueError('incomplete gzip')
    return raw, d.unused_data


REVISION_NAMES = ('preview', 'global', 'history', 'elemTable', 'contentDocuments',
                  'partitionTable', 'incrementTable', 'basicFileInfo',
                  'transmissionData', 'partAtom', 'projectXMLInfo')


def revision_spans(raw, evidence):
    root = evidence['contents_root']
    if (hashlib.sha256(raw).hexdigest() != evidence['contents_inflated_sha256']
            or root['class_name'] != 'DocumentStorageIndexImpl'
            or root['class_tag'] not in (1250, 1285, 1315)
            or struct.unpack_from('<H', raw)[0] != root['class_tag']):
        raise ValueError('Contents schema evidence mismatch')
    spans = {}
    group = [s for s in root['field_spans'] if s['name'] == 'm_streamRevisions']
    if len(group) != 1:
        raise ValueError('ambiguous revision group')
    for name in REVISION_NAMES:
        key = f'm_{name}StreamRevision'
        found = [s for s in root['field_spans'] if s['name'] == key]
        if len(found) != 1:
            raise ValueError('missing/ambiguous revision span')
        span = found[0]; start, end = span['start'], span['end']
        if not group[0]['start'] <= start < end <= group[0]['end'] <= len(raw) or end-start != 4:
            raise ValueError('invalid revision span')
        if struct.unpack_from('<i', raw, start)[0] != root['fields']['m_streamRevisions'][key]:
            raise ValueError('revision span value disagrees')
        spans[name] = (start, end)
    occupied = [i for start, end in spans.values() for i in range(start, end)]
    if len(set(occupied)) != len(occupied):
        raise ValueError('overlapping revision spans')
    return spans


def patch_contents_payload(logical, evidence, revisions):
    """Patch only schema-proven revision spans; return unpaged logical Contents.

    `revisions` uses short names such as history/elemTable. Formats is the
    observed final wrapper u32, whose equality is independently corpus-tested.
    This synchronizes values; it does not decide which revisions a save needs.
    """
    if hashlib.sha256(logical).hexdigest() != evidence['contents_logical_sha256']:
        raise ValueError('Contents source changed')
    if set(revisions) - set(REVISION_NAMES) - {'formats'}:
        raise ValueError('unknown revision name')
    header = bytes.fromhex(evidence['contents_header_hex'])
    if not logical.startswith(header) or len(header) not in (24, 91):
        raise ValueError('unsupported Contents wrapper')
    raw, suffix = inflated(logical, len(header))
    if suffix:
        raise ValueError('unexpected logical Contents gzip suffix')
    spans = revision_spans(raw, evidence)
    changed = bytearray(raw); changed_header = bytearray(header)
    for name, value in revisions.items():
        if type(value) is not int:
            raise ValueError('revision must be an integer')
        try:
            if name == 'formats':
                struct.pack_into('<i', changed_header, len(header)-4, value)
            else:
                struct.pack_into('<i', changed, spans[name][0], value)
        except struct.error as error:
            raise ValueError('revision outside int32') from error
    if changed == raw and changed_header == header:
        return logical
    gzip_header = logical[len(header):len(header)+10]
    if len(gzip_header) != 10 or gzip_header[:4] != b'\x1f\x8b\x08\x00':
        raise ValueError('unsupported gzip header')
    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(changed)+compressor.flush()
    result = (bytes(changed_header)+gzip_header+compressed
              + struct.pack('<II', zlib.crc32(changed), len(changed)))
    check, suffix = inflated(result, len(header))
    if check != changed or suffix:
        raise ValueError('Contents encode verification failed')
    return result


def patch_basic_file_info(source, evidence, increments, document_guid=None):
    """Update paired fixed-width counter properties and optionally paired GUIDs.

    Source hash and exact property spans must match independent reader evidence.
    Binary fields are preserved and their relationship to counters is unproven.
    """
    if hashlib.sha256(source).hexdigest() != evidence['basic_file_info_sha256']:
        raise ValueError('BasicFileInfo source changed')
    if type(increments) is not int or not 0 <= increments <= 0x7fffffff:
        raise ValueError('invalid document increment count')
    keys = ('Unique Document Increments',
            "Central model's version number corresponding to the last reload latest")
    values = {key: str(increments) for key in keys}
    if document_guid is not None:
        try:
            canonical = str(uuid.UUID(document_guid))
        except (ValueError, AttributeError, TypeError) as error:
            raise ValueError('invalid document GUID') from error
        values['Unique Document GUID'] = canonical
        values["Central model's episode GUID corresponding to the last reload latest"] = canonical
    changes = []
    for key, new_value in values.items():
        replacement = new_value.encode('utf-16-le')
        span = evidence['basic_file_info_property_spans'][key]
        start, end = span['start'], span['end']
        old = span['value'].encode('utf-16-le')
        prefix = (key+': ').encode('utf-16-le')
        if (not len(prefix) <= start < end <= len(source)
                or source[start:end] != old
                or source[start-len(prefix):start] != prefix
                or source[end:end+4] != b'\r\x00\n\x00'
                or (key in keys and (not span['value'].isascii() or not span['value'].isdigit()
                    or int(span['value']) != evidence['document_increments']))
                or (key not in keys and span['value'] != evidence['document_guid'])):
            raise ValueError('BasicFileInfo property span disagrees')
        if len(replacement) != end-start:
            raise ValueError('variable-width BasicFileInfo counter edit unsupported')
        changes.append((start, end, replacement))
    ordered = sorted(changes)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('overlapping BasicFileInfo properties')
    result = bytearray(source)
    for start, end, replacement in changes:
        result[start:end] = replacement
    return bytes(result)


def run(source, files, target):
    source = source.resolve()
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'], check=True)
    local = Path(__file__).resolve().parent/'local'
    with tempfile.TemporaryDirectory(dir=local) as temp:
        project = Path(temp); (project/'src').mkdir()
        (project/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
        (project/'Cargo.toml').write_text('[package]\nname="rvt-save-identity-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo', 'build', '--release', '--offline', '--manifest-path', str(project/'Cargo.toml'), '--target-dir', str(target.resolve())], check=True)
        reports = []
        for path in files:
            with olefile.OleFileIO(path) as f:
                contents_stored = f.openstream('Contents').read()
                contents = unpage(contents_stored)
                gzip_offset = contents.index(b"\x1f\x8b\x08")
                raw, suffix = inflated(contents, gzip_offset)
                schema, _ = inflated(unpage(f.openstream('Formats/Latest').read()), 0)
                basic = f.openstream('BasicFileInfo').read()
                latest_bytes, _ = inflated(unpage(f.openstream('Global/Latest').read()), 8)
                (project/'latest.bin').write_bytes(latest_bytes)
                for name, data in [('schema', schema), ('contents', raw), ('basic', basic)]:
                    (project/(name+'.bin')).write_bytes(data)
                result = json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-save-identity-probe'), str(project)]))
                increments = increments_decode(inflated(unpage(f.openstream('Global/DocumentIncrementTable').read()), 8)[0])[1]['m_increments']
                history = history_decode(inflated(unpage(f.openstream('Global/History').read()), 8)[0])
                latest = increments[-1]
                props = {x['key']: x['value'] for x in result.pop('properties')}
                selected = ('Unique Document GUID', 'Unique Document Increments',
                    "Central model's version number corresponding to the last reload latest",
                    "Central model's episode GUID corresponding to the last reload latest")
                property_spans = {}
                for key in selected:
                    needle = (key+': '+props[key]).encode('utf-16-le')
                    starts = [i for i in range(len(basic)) if basic.startswith(needle, i)]
                    if len(starts) != 1:
                        raise ValueError('ambiguous BasicFileInfo property')
                    start = starts[0]+len((key+': ').encode('utf-16-le'))
                    property_spans[key] = {'value': props[key], 'start': start,
                                          'end': start+len(props[key].encode('utf-16-le'))}
                guid = uuid.UUID(result['document_guid']).bytes_le
                guid_matches = [name for name, value in zip(GUID_NAMES, history.guids) if value == guid]
                revisions = result['contents_root']['fields']['m_streamRevisions']
                relationships = {
                    'contents_revisions_equal_latest_increment': all(latest[k] == v for k, v in revisions.items()),
                    'wrapper_formats_revision_equals_latest_increment': struct.unpack_from('<i', contents, gzip_offset-4)[0] == latest['m_formatsStreamRevision'],
                    'document_increments_equal_increment_entries': result['document_increments'] == len(increments),
                    'document_increments_equal_latest_major_version': result['document_increments'] == latest['m_majorVersion'],
                    'reload_latest_version_equals_document_increments': int(props[selected[2]]) == result['document_increments'],
                    'reload_latest_guid_equals_document_guid': props[selected[3]] == result['document_guid'],
                    'document_guid_equals_newest_history_episode': bool(history.episodes) and history.episodes[0][:16] == guid}
                result.update(basic_file_info_property_spans=property_spans,
                    basic_file_info_sha256=hashlib.sha256(basic).hexdigest(),
                    document_guid_matching_history_fields=guid_matches,
                    contents_formats_revision=struct.unpack_from('<i', contents, gzip_offset-4)[0],
                    relationships=relationships,
                    limitations=['No paired saves establish GUID changes or counter allocation rules.',
                      'BasicFileInfo property spans identify text only, not all binary duplicates.',
                      'Global/Latest complete wire graph decoding does not establish every field semantic.',
                      'Identity-name filtering covers top-level object fields, not every possible semantic reference.',
                      'Contents root decoder stops before opaque trailing bytes; patcher preserves them.'])
                reports.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'reader_commit': REV, 'contents_stored_bytes': len(contents_stored),
                    'contents_logical_bytes': len(contents),
                    'contents_inflated_sha256': hashlib.sha256(raw).hexdigest(),
                    'contents_logical_sha256': hashlib.sha256(contents).hexdigest(),
                    'contents_header_hex': contents[:gzip_offset].hex(), 'contents_gzip_suffix_hex': suffix.hex(),
                    'contents_inflated_bytes': len(raw), 'contents_inflated_hex': raw.hex(), **result})
                evidence = reports[-1]
                revision_spans(raw, evidence)
                if patch_contents_payload(contents, evidence, {}) != contents:
                    raise ValueError('Contents identity patch differed')
                evidence['identity_patch_byte_exact'] = True
                trial = {name: revisions[f'm_{name}StreamRevision']+1 for name in REVISION_NAMES}
                patched = patch_contents_payload(contents, evidence, trial)
                trial_raw, _ = inflated(patched, gzip_offset)
                (project/'contents.bin').write_bytes(trial_raw)
                trial_result = json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-save-identity-probe'), str(project)]))
                expected_fields = json.loads(json.dumps(result['contents_root']['fields']))
                expected_fields['m_streamRevisions'] = {f'm_{name}StreamRevision': value for name, value in trial.items()}
                if trial_result['contents_root']['fields'] != expected_fields:
                    raise ValueError('independent decoder rejects revision-only trial')
                evidence['all_revision_spans_trial_independently_verified'] = True
                trial_guid = str(uuid.UUID('01234567-89ab-4cde-8f01-23456789abcd'))
                trial_basic = patch_basic_file_info(basic, evidence, result['document_increments']+1, trial_guid)
                (project/'basic.bin').write_bytes(trial_basic)
                trial_info = json.loads(subprocess.check_output([str(target.resolve()/'release/rvt-save-identity-probe'), str(project)]))
                trial_props = {x['key']: x['value'] for x in trial_info['properties']}
                expected_props = dict(props)
                expected_props['Unique Document Increments'] = str(result['document_increments']+1)
                expected_props["Central model's version number corresponding to the last reload latest"] = str(result['document_increments']+1)
                expected_props['Unique Document GUID'] = trial_guid
                expected_props["Central model's episode GUID corresponding to the last reload latest"] = trial_guid
                if trial_props != expected_props or trial_info['document_guid'] != trial_guid:
                    raise ValueError('independent BasicFileInfo trial differs')
                evidence['fixed_width_counter_trial_independently_verified'] = True
        return reports


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source', type=Path, required=True)
    p.add_argument('--target', type=Path, required=True)
    p.add_argument('files', type=Path, nargs='+')
    a = p.parse_args()
    print(json.dumps(run(a.reader_source, a.files, a.target), indent=2))
