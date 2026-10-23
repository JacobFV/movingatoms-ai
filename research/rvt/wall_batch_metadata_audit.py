"""Independent raw table/History and coordinated metadata audit for batch walls.

Builder plans are cross-checks, never authorities for preserved source bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import uuid
import zlib
import olefile
from codec import decode as unpage
from save_increments import decode as increments_decode, REVISIONS
from partition_segments import decode as partition_decode
from partition_objects import validate as objects_validate
from basic_file_info_codec import decode as basic_decode
from project_information_codec import parse as project_parse
from datetime import datetime
from pages import CORE_SHA256


def sha(data): return hashlib.sha256(data).hexdigest()


def inflate_global(stored):
    logical = unpage(stored); d = zlib.decompressobj(31); raw = d.decompress(logical[8:])
    if not d.eof or d.unconsumed_tail: raise ValueError('invalid global gzip')
    return raw


def table_parts(raw):
    if len(raw) < 30: raise ValueError('truncated table')
    tag, count = struct.unpack_from('<HI', raw)
    stop = 6+40*count
    if stop+24 != len(raw): raise ValueError('unsupported table framing')
    rows = [raw[i:i+40] for i in range(6, stop, 40)]; tail = raw[stop:]
    if tail[:8] != b'\0'*4+b'\xff'*4 or tail[10:12] != b'\0\0' or tail[20:] != b'\0'*4:
        raise ValueError('unsupported table trailer')
    ids = [struct.unpack_from('<Q', row, 20)[0] for row in rows]
    if ids != sorted(set(ids)): raise ValueError('duplicate or unordered table IDs')
    last = struct.unpack_from('<Q', tail, 12)[0]
    if ids and ids[-1] > last: raise ValueError('table identifier ceiling below records')
    return tag, rows, tail, last


def audit_table(old_raw, new_raw, episode):
    old_tag, old_rows, old_tail, last = table_parts(old_raw)
    new_tag, new_rows, new_tail, new_last = table_parts(new_raw)
    count = len(new_rows)-len(old_rows)
    if count <= 0 or new_tag != old_tag or new_rows[:len(old_rows)] != old_rows:
        raise ValueError('source table records changed or no new rows')
    expected_ids = list(range(last+1, last+count+1))
    expected_tail = bytearray(old_tail); struct.pack_into('<Q', expected_tail, 12, expected_ids[-1])
    if new_tail != expected_tail: raise ValueError('unexpected identifier trailer changes')
    for row, ident in zip(new_rows[len(old_rows):], expected_ids):
        actual = struct.unpack('<QIIIQQI', row)
        if actual != (ident, episode, episode, episode, ident, 0xffffffffffffffff, 0):
            raise ValueError('new row identity/creation/modification/owner differs')
    return {'new_ids': expected_ids, 'source_rows': len(old_rows), 'candidate_rows': len(new_rows),
            'source_identifier_ceiling': last, 'candidate_identifier_ceiling': new_last,
            'all_source_rows_byte_identical': True, 'new_row_episode_fields': [episode]*3}


def history_parts(raw):
    if len(raw) < 114: raise ValueError('truncated History')
    tag = struct.unpack_from('<H', raw)[0]
    if tag not in (1244, 1279, 1309): raise ValueError('unsupported History tag')
    document, increments, inline_count, sequence, deficit = struct.unpack_from('<IIIii', raw, 2)
    if document not in (0, 1) or increments not in (0, 1) or inline_count or deficit:
        raise ValueError('unsupported History fields')
    upgrades = struct.unpack_from('<I', raw, 102)[0]
    count_offset = 106+4*upgrades
    if count_offset+4 > len(raw): raise ValueError('truncated History upgrade list')
    count = struct.unpack_from('<I', raw, count_offset)[0]; start = count_offset+4
    if sequence != count or start+17*count+4 != len(raw) or raw[-4:] != b'\0'*4:
        raise ValueError('History count or sequence disagrees')
    records = [raw[i:i+17] for i in range(start, len(raw)-4, 17)]
    if any(record[-1] != 0x28 for record in records): raise ValueError('unsupported episode strength')
    return count_offset, start, sequence, records


def audit_history(old, new):
    offset, start, episode, old_records = history_parts(old)
    new_offset, new_start, next_episode, new_records = history_parts(new)
    if (offset, start, episode+1) != (new_offset, new_start, next_episode):
        raise ValueError('expected exactly one History episode')
    prefix = bytearray(old[:start]); struct.pack_into('<i', prefix, 14, next_episode)
    struct.pack_into('<I', prefix, offset, next_episode)
    if new[:start] != prefix or new[start+17:] != old[start:]:
        raise ValueError('preexisting History bytes changed')
    guid = new_records[0][:16]
    if guid == b'\0'*16 or guid in [r[:16] for r in old_records]: raise ValueError('new episode GUID is not fresh')
    return {'creation_episode': episode, 'new_history_count': next_episode,
            'new_episode_guid': str(uuid.UUID(bytes_le=guid)),
            'all_old_episode_records_and_history_metadata_preserved': True}


def registration_check(old, new, ids, evidence):
    if not ids or ids != sorted(set(ids)): raise ValueError('new registration IDs must be sorted unique')
    evidence = evidence.get('source_evidence', evidence)
    if sha(old) != evidence['inflated_sha256']: raise ValueError('source registration evidence hash differs')
    obj = evidence['object']
    if obj['class_name'] != 'StructuralElemSetTracking': raise ValueError('wrong registration schema class')
    spans = [s for s in obj['field_spans'] if s['name'] == 'm_elemIdSet']
    if len(spans) != 1: raise ValueError('ambiguous structural registration span')
    start, end = spans[0]['start'], spans[0]['end']
    count = struct.unpack_from('<I', old, start)[0]
    if end != start+4+8*count: raise ValueError('registration array framing differs')
    existing = list(struct.unpack_from('<'+'q'*count, old, start+4))
    if existing != sorted(set(existing)) or set(existing)&set(ids): raise ValueError('duplicate registration IDs')
    expected = sorted(existing+ids)
    expected_bytes = struct.pack('<I', len(expected))+struct.pack('<'+'q'*len(expected), *expected)
    if new != old[:start]+expected_bytes+old[end:]: raise ValueError('unexpected Global registration changes')
    return {'prior_registered_ids': len(existing), 'new_registered_ids': ids,
            'all_other_inflated_global_bytes_identical': True, 'sorted_unique_union': True}


def run(source, candidate, plan, identity_evidence, registration_evidence):
    source_sha, candidate_sha = sha(source.read_bytes()), sha(candidate.read_bytes())
    if source_sha != CORE_SHA256: raise ValueError('requires pinned source fixture')
    with olefile.OleFileIO(source) as old, olefile.OleFileIO(candidate) as new:
        old_names, new_names = {tuple(p) for p in old.listdir()}, {tuple(p) for p in new.listdir()}
        history = audit_history(inflate_global(old.openstream('Global/History').read()), inflate_global(new.openstream('Global/History').read()))
        table = audit_table(inflate_global(old.openstream('Global/ElemTable').read()), inflate_global(new.openstream('Global/ElemTable').read()), history['creation_episode'])
        ids = table['new_ids']; count = len(ids)
        _, prior = increments_decode(inflate_global(old.openstream('Global/DocumentIncrementTable').read()))
        _, changed = increments_decode(inflate_global(new.openstream('Global/DocumentIncrementTable').read()))
        if prior['m_permutation'] or changed['m_permutation']: raise ValueError('increment permutations unsupported')
        if changed['m_increments'] != changed['m_localIncrements']: raise ValueError('increment arrays differ')
        ordinal = len(prior['m_increments']); stream = f'Partitions/{ordinal}'
        for array in ('m_increments', 'm_localIncrements'):
            rows = changed[array]; previous = prior[array]
            if len(rows) != len(previous)+1 or rows[:-1] != previous: raise ValueError('preexisting increment records changed')
            last = rows[-1]
            if (last['m_totalElements'] != count or last['m_incrementVersions'] != [{'m_causedByIncrementNumber': -1, 'm_totalElements': count}]
                    or last['m_greatest']['m_id'] != history['creation_episode'] or last['m_totalEpisodes'] != history['new_history_count']
                    or last['m_majorVersion'] != previous[-1]['m_majorVersion']+1 or last['m_overwrite']):
                raise ValueError('batch increment cardinality or episode differs')
        latest = changed['m_increments'][-1]; old_latest = prior['m_increments'][-1]
        if latest['m_atimeStamp']['m_msb'] != 0 or latest['m_atimeStamp']['m_lsb'] <= old_latest['m_atimeStamp']['m_lsb']:
            raise ValueError('batch timestamp does not follow source')
        revisions = {}
        for name in REVISIONS:
            key = f'm_{name}StreamRevision'; delta = latest[key]-old_latest[key]
            expected_delta = 0 if name in ('preview', 'formats', 'partAtom') else 1
            if delta != expected_delta: raise ValueError('unexpected selected stream revision policy: '+name)
            revisions[name] = delta
        if new_names-old_names != {tuple(stream.split('/'))} or old_names-new_names: raise ValueError('unexpected stream creation/deletion')
        changed_streams = []
        for parts in old_names:
            if old.openstream(parts).read() != new.openstream(parts).read(): changed_streams.append('/'.join(parts))
        expected_changes = {'Global/History', 'Global/ElemTable', 'Global/DocumentIncrementTable', 'Global/Latest', 'Contents', 'BasicFileInfo', 'ProjectInformation'}
        if set(changed_streams) != expected_changes: raise ValueError('unexpected changed stream set')
        partition = partition_decode(unpage(new.openstream(stream).read()))
        if len(partition.segments) != 1 or partition.segments[0].guid is not None or partition.segments[0].count != count:
            raise ValueError('unexpected new partition group count')
        records = objects_validate(partition.segments[0], 8)
        body_hashes = {}
        for channel, values in records.items():
            if [r.element_id for r in values] != ids+[0xffffffffffffffff] or values[-1].body:
                raise ValueError('partition ID order or terminal sentinel differs')
            body_hashes[str(channel)] = {str(r.element_id): sha(r.body) for r in values[:-1]}
        registration = registration_check(inflate_global(old.openstream('Global/Latest').read()), inflate_global(new.openstream('Global/Latest').read()), ids, registration_evidence)
        basic = basic_decode(new.openstream('BasicFileInfo').read())
        if basic.increments != ordinal+1 or basic.guid != history['new_episode_guid']: raise ValueError('binary/text BasicFileInfo identity disagrees')
        evidence = next(e for e in identity_evidence if e['sha256'] == source_sha)
        logical = unpage(new.openstream('Contents').read()); header = bytes.fromhex(evidence['contents_header_hex'])
        d = zlib.decompressobj(31); contents = d.decompress(logical[len(header):])
        if not d.eof or d.unused_data: raise ValueError('invalid Contents gzip')
        old_logical = unpage(old.openstream('Contents').read())
        old_decoder = zlib.decompressobj(31); original_contents = old_decoder.decompress(old_logical[len(header):])
        if (not old_decoder.eof or old_decoder.unused_data or old_logical[:len(header)] != header
                or sha(original_contents) != evidence['contents_inflated_sha256']):
            raise ValueError('source Contents evidence differs from actual bytes')
        expected_contents = bytearray(original_contents)
        for span in evidence['contents_root']['field_spans']:
            key = span['name']
            if key.startswith('m_') and key.endswith('StreamRevision'):
                if span['end']-span['start'] != 4: raise ValueError('revision span width')
                struct.pack_into('<i', expected_contents, span['start'], latest[key])
        expected_header = bytearray(header); struct.pack_into('<i', expected_header, len(header)-4, latest['m_formatsStreamRevision'])
        if contents != expected_contents or logical[:len(header)] != expected_header: raise ValueError('Contents revisions or opaque bytes differ')
        _, old_stamp, *_ = project_parse(old.openstream('ProjectInformation').read())
        _, new_stamp, *_ = project_parse(new.openstream('ProjectInformation').read())
        offset_before = old_latest['m_atimeStamp']['m_lsb']-int(datetime.fromisoformat(old_stamp).timestamp())
        offset_after = latest['m_atimeStamp']['m_lsb']-int(datetime.fromisoformat(new_stamp).timestamp())
        if offset_before != offset_after: raise ValueError('ProjectInformation offset changed')
    if plan['source_sha256'] != source_sha or plan['new_element_ids'] != ids or plan['new_episode_guid'] != history['new_episode_guid'] or plan['new_partition'] != stream:
        raise ValueError('plan claims differ from actual candidate')
    if [wall['id'] for wall in plan['walls']] != ids: raise ValueError('plan walls differ from actual ID set')
    for wall in plan['walls']:
        for channel, expected in wall['body_sha256'].items():
            if body_hashes[channel][str(wall['id'])] != expected: raise ValueError('actual body differs from planned bytes')
    return {'source_sha256': source_sha, 'candidate_sha256': candidate_sha,
        'plan_sha256': sha(json.dumps(plan, sort_keys=True).encode()), 'table': table, 'history': history,
        'new_partition': stream, 'new_increment_total_elements': count,
        'new_increment_version_total_elements': count, 'all_preexisting_increment_rows_preserved': True,
        'all_original_partition_streams_byte_identical': True, 'changed_existing_streams': sorted(changed_streams),
        'registration': registration, 'body_sha256': body_hashes,
        'basic_file_info_all_identity_copies_agree': True, 'contents_revisions_match_latest_increment': True,
        'revision_deltas': revisions, 'project_information_offset_seconds': offset_after,
        'limitations': ['Episode allocation and revision policies remain explicit candidate hypotheses.',
            'Typed body self/external references and native geometry are checked by separate independent graph audit.',
            'No native Autodesk acceptance result.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('candidate', type=Path); p.add_argument('plan', type=Path)
    p.add_argument('--result', type=Path)
    a = p.parse_args(); results = Path(__file__).parent/'results'
    report = run(a.source, a.candidate, json.loads(a.plan.read_bytes()),
                 json.loads((results/'save-identity.json').read_bytes()), json.loads((results/'wall-element-registration.json').read_bytes()))
    text = json.dumps(report, indent=2)+'\n'
    if a.result:
        with a.result.open('x') as output: output.write(text)
    else: print(text, end='')
