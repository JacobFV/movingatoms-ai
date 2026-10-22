"""Pinned unsigned append-save hypothesis, never an Autodesk-validated save.

Preserves old partitions and inserts one changed existing room into a new
increment. Revision allocation and old-record retention are explicit hypotheses.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import uuid
import zlib
import olefile
from codec import decode as unpage
import element_table
import save_history
import save_increments
from partition_segments import decode as partition_decode, encode as partition_encode
from partition_objects import validate
from partition_builder import build_partition
from data_objects import replace_record_text
from parameter_experiment import SOURCE_SHA, STREAM, ELEMENT, PARAMETER, recompress

GUID = uuid.UUID('5f197eb7-5987-5937-94d9-99f5208ac16c')
HYPOTHESES = [
    'New append increment ordinal 85 maps to Partitions/85.',
    'A modification sets only ElemTable m_history.m_lastModificationDate to new episode 703; creation fields and m_lastUserModificationDate remain unchanged (unverified assumption).',
    'Old physical records and increment counts remain as historical storage; no compaction is performed.',
    'New increment stores one project element and no content groups; both identical increment arrays append the same row.',
    'Changed global/history/elemTable/partitionTable/incrementTable revisions advance prior values by one.',
    'Other stream revisions and bytes remain unchanged, except the explicit BasicFileInfo synchronization variant; complete save state is not reconstructed.',
    'Empty signature fields are an experimental unsigned encoding, with unknown Revit acceptance.',
]


def unpack_global(logical):
    if logical[8:12] != b'\x1f\x8b\x08\x00': raise ValueError('unsupported global gzip envelope')
    d = zlib.decompressobj(31); body = d.decompress(logical[8:])
    if not d.eof or d.unconsumed_tail: raise ValueError('incomplete global gzip')
    return body, d.unused_data


def repack_global(logical, body):
    _, suffix = unpack_global(logical)
    return logical[:8] + recompress(logical[8:], body) + suffix


def append_increment(fields, episode, timestamp):
    """Explicit static-file hypothesis, not a discovered save algorithm."""
    if fields['m_increments'] != fields['m_localIncrements'] or fields['m_permutation']:
        raise ValueError('requires identical unpermuted increment arrays')
    old = fields['m_increments']
    if not old or old[-1]['m_greatest']['m_id'] + 1 != episode:
        raise ValueError('episode does not follow prior increment')
    if old[-1]['m_atimeStamp']['m_msb'] != 0: raise ValueError('unsupported high timestamp word')
    if not 0 <= timestamp <= 0xffffffff or timestamp <= old[-1]['m_atimeStamp']['m_lsb']:
        raise ValueError('timestamp must follow source and fit observed low word')
    row = deepcopy(old[-1])
    row.update(m_incrementVersions=[{'m_causedByIncrementNumber': -1, 'm_totalElements': 1}],
               m_userName='clean-room research', m_comment='Unsigned append-save hypothesis',
               m_greatest={'m_id': episode}, m_totalEpisodes=episode+1,
               m_atimeStamp={'m_msb': 0, 'm_lsb': timestamp},
               m_majorVersion=row['m_majorVersion']+1, m_totalElements=1, m_overwrite=False)
    for name in ('global', 'history', 'elemTable', 'partitionTable', 'incrementTable'):
        key = f'm_{name}StreamRevision'
        if row[key] < 0: raise ValueError('cannot allocate absent stream revision')
        row[key] += 1
    result = deepcopy(fields)
    for name in ('m_increments', 'm_localIncrements'): result[name].append(deepcopy(row))
    return result


def make(source, dest, *, acknowledge_hypotheses=False, timestamp=1792627200, contents_evidence=None, update_basic_file_info=False, update_document_guid=False, synchronize_binary_identity=False):
    if not acknowledge_hypotheses: raise ValueError('explicit hypothesis acknowledgment required')
    if synchronize_binary_identity and not (update_basic_file_info and update_document_guid):
        raise ValueError('binary identity synchronization requires both BasicFileInfo synchronization flags')
    if update_document_guid and not update_basic_file_info:
        raise ValueError('document GUID update requires BasicFileInfo synchronization')
    if update_basic_file_info and contents_evidence is None:
        raise ValueError('BasicFileInfo update requires Contents schema evidence')
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('requires pinned MIT Architecture fixture')
    names = ['Global/History', 'Global/ElemTable', 'Global/DocumentIncrementTable']
    with olefile.OleFileIO(source) as f:
        stored = {name: f.openstream(name).read() for name in names}
        original_contents = f.openstream('Contents').read()
        original_basic = f.openstream('BasicFileInfo').read()
        partition = partition_decode(unpage(f.openstream(STREAM).read()))
        if f.exists('Partitions/85'): raise ValueError('new partition already exists')
    logical = {n: unpage(b) for n, b in stored.items()}
    bodies = {n: unpack_global(b)[0] for n, b in logical.items()}
    history = save_history.decode(bodies[names[0]])
    table = element_table.decode(bodies[names[1]], 8)
    tag, fields = save_increments.decode(bodies[names[2]])
    if len(fields['m_increments']) != 85 or history.next_sequence != 703:
        raise ValueError('pinned source save state differs')
    records = validate(partition.segments[0], 8)
    selected = {seq: tuple(r for r in values if r.element_id == ELEMENT) for seq, values in records.items()}
    if any(len(v) != 1 for v in selected.values()): raise ValueError('nonunique source room')
    selected[102] = (replace_record_text(selected[102][0], PARAMETER, 'Wood', 'Polished concrete'),)
    new_partition = build_partition(partition.root_tag, selected, 8, allow_unsigned_nonempty=True)
    row_index = next(i for i, row in enumerate(table.rows) if table.current(row) == ELEMENT)
    old_row = table.rows[row_index]
    if struct.unpack('<QIIIQQI', old_row) != (ELEMENT, 639, 687, 639, ELEMENT, 2**64-1, 0):
        raise ValueError('pinned room row differs')
    new_row = bytearray(old_row); struct.pack_into('<I', new_row, 12, history.next_sequence)
    rows = list(table.rows); rows[row_index] = bytes(new_row)
    revised = append_increment(fields, history.next_sequence, timestamp)
    if update_basic_file_info:
        for name in ('m_increments', 'm_localIncrements'):
            revised[name][-1]['m_basicFileInfoStreamRevision'] += 1
    replacements = {
        names[0]: save_history.encode(save_history.prepend_episode(history, GUID.bytes_le)),
        names[1]: element_table.encode(replace(table, rows=tuple(rows))),
        names[2]: save_increments.encode(tag, revised),
    }
    dest.mkdir(parents=True, exist_ok=False)
    patches = []
    for name, body in replacements.items():
        filename = name.split('/')[-1]+'.bin'
        (dest/filename).write_bytes(repack_global(logical[name], body))
        patches.append({'stream': name, 'expected_stored_sha256': hashlib.sha256(stored[name]).hexdigest(),
                        'new_payload_file': filename})
    if contents_evidence is not None:
        from save_identity import patch_contents_payload
        if isinstance(contents_evidence, list):
            matches = [e for e in contents_evidence if e['sha256'] == SOURCE_SHA]
            if len(matches) != 1: raise ValueError('requires one pinned source Contents evidence item')
            contents_evidence = matches[0]
        if contents_evidence['sha256'] != SOURCE_SHA: raise ValueError('Contents evidence fixture mismatch')
        revisions = {name:revised['m_increments'][-1][f'm_{name}StreamRevision']
                     for name in save_increments.REVISIONS}
        contents = patch_contents_payload(unpage(original_contents), contents_evidence, revisions)
        (dest/'Contents.bin').write_bytes(contents)
        patches.append({'stream':'Contents', 'expected_stored_sha256':hashlib.sha256(original_contents).hexdigest(),
                        'new_payload_file':'Contents.bin'})
    if update_basic_file_info:
        from save_identity import patch_basic_file_info
        if synchronize_binary_identity:
            import basic_file_info_codec
            basic = basic_file_info_codec.encode(basic_file_info_codec.decode(original_basic),
                increments=len(revised['m_increments']), document_guid=str(GUID))
        else:
            basic = patch_basic_file_info(original_basic, contents_evidence, len(revised['m_increments']),
                                          document_guid=str(GUID) if update_document_guid else None)
        (dest/'BasicFileInfo.bin').write_bytes(basic)
        patches.append({'stream':'BasicFileInfo', 'expected_stored_sha256':hashlib.sha256(original_basic).hexdigest(),
                        'new_payload_file':'BasicFileInfo.bin'})
    (dest/'partition.bin').write_bytes(partition_encode(new_partition))
    manifest = {'input_sha256': SOURCE_SHA, 'patches': patches, 'creates': [
        {'stream': 'Partitions/85', 'expected_absent': True, 'new_payload_file': 'partition.bin'}]}
    (dest/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return {'source_sha256': SOURCE_SHA, 'new_stream': 'Partitions/85', 'element': ELEMENT,
            'new_episode': 703, 'episode_guid': str(GUID), 'timestamp': timestamp,
            'table_changed_offsets': [i for i, (a,b) in enumerate(zip(old_row,new_row)) if a != b],
            'new_partition_records_per_sequence': 1, 'signature_fields': 'empty',
            'contents_revisions_synchronized': contents_evidence is not None,
            'basic_file_info_counts_synchronized': update_basic_file_info,
            'basic_file_info_guid_synchronized': update_document_guid,
            'basic_file_info_binary_duplicates_synchronized': synchronize_binary_identity,
            'hypotheses': HYPOTHESES + (['BasicFileInfo counters update to86 and its revision increments; structural binary duplicates synchronize only with explicit flag; other binary fields remain opaque.'] if update_basic_file_info else []), 'complete_save_transaction': False,
            'autodesk_acceptance': 'not_tested', 'production_native_export': False}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('dest', type=Path)
    p.add_argument('--acknowledge-hypotheses', action='store_true')
    p.add_argument('--timestamp', type=int, default=1792627200)
    p.add_argument('--update-basic-file-info', action='store_true')
    p.add_argument('--update-document-guid', action='store_true')
    p.add_argument('--synchronize-binary-identity', action='store_true')
    p.add_argument('--contents-evidence', type=Path, help='independent schema evidence for synchronized Contents variant')
    a = p.parse_args(); print(json.dumps(make(a.source, a.dest,
        acknowledge_hypotheses=a.acknowledge_hypotheses, timestamp=a.timestamp,
        contents_evidence=json.loads(a.contents_evidence.read_bytes()) if a.contents_evidence else None,
        update_basic_file_info=a.update_basic_file_info, update_document_guid=a.update_document_guid, synchronize_binary_identity=a.synchronize_binary_identity), indent=2))
