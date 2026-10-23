"""Pinned multi-wall append research transaction; native acceptance remains untested."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import uuid
import zlib
import olefile
import wall_candidate as c
from wall_parametric import encode_wall
from wall_element_registration import register
from new_element_registration import id_set_bytes

DEMO_SPECS = [{'length_feet': n, 'translation_xy': [x, 0.0]} for n, x in [(6.0, 400.0), (12.0, 430.0), (18.0, 470.0)]]
SOURCE_MAX_X = 379.02599533649595  # All current saved header boxes: wall-element-bounds.json.


def validate_specs(specs):
    if not isinstance(specs, list) or not 1 <= len(specs) <= 100:
        raise ValueError('requires 1..100 wall specifications')
    result = []
    for spec in specs:
        if not isinstance(spec, dict) or set(spec) != {'length_feet', 'translation_xy'}:
            raise ValueError('spec requires exactly length_feet and translation_xy')
        length, xy = spec['length_feet'], spec['translation_xy']
        if type(length) not in (int, float) or not math.isfinite(length) or not 0.01 <= length <= 10000:
            raise ValueError('unsupported finite wall length')
        if not isinstance(xy, (list, tuple)) or len(xy) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 100000 for v in xy):
            raise ValueError('requires finite bounded XY translation')
        normalized = {'length_feet': float(length), 'translation_xy': list(map(float, xy))}
        if normalized in result:
            raise ValueError('duplicate wall specification')
        result.append(normalized)
    return result


def prepare_walls(profile, specs, first_id=133210):
    specs = validate_specs(specs)
    walls = []
    for offset, spec in enumerate(specs):
        ident = first_id + offset
        bodies, graphs, audit = encode_wall(profile, ident, length_feet=spec['length_feet'],
            translation_xy=spec['translation_xy'], context=profile['external_references'],
            room_bounding=False, acknowledge_bounding_hypothesis=True)
        bbox = graphs['103']['objects'][0]['fields']['m_bBox']
        if not bbox[0][0] > SOURCE_MAX_X + 1:
            raise ValueError('wall must lie east of all source saved header boxes with one foot clearance')
        if any(not any(bbox[1][i] < w['bbox'][0][i] or w['bbox'][1][i] < bbox[0][i] for i in range(3)) for w in walls):
            raise ValueError('new wall bounds intersect or touch')
        walls.append({'id': ident, 'spec': spec, 'bodies': bodies, 'bbox': bbox, 'audit': audit})
    return walls


def register_batch(raw, evidence, ids):
    if not ids or len(ids) != len(set(ids)) or any(type(v) is not int or not 0 < v < 2**31 for v in ids):
        raise ValueError('requires distinct positive IDs')
    _, change = register(raw, evidence, ids[0])
    old = change['ids_before']
    if set(old).intersection(ids):
        raise ValueError('new ID already registered')
    span = change['span_before']
    after = sorted(old + ids)
    return raw[:span['start']] + id_set_bytes(after) + raw[span['end']:], {**change, 'ids_after': after}


def make(source, dest, profile, identity_evidence, registration_evidence, specs, *, acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:
        raise ValueError('explicit unsigned/save/nonbounding/batch hypotheses acknowledgment required')
    # Every request and binary payload is checked before creating any output directory.
    walls = prepare_walls(profile, specs)
    source, dest = Path(source), Path(dest)
    if hashlib.sha256(source.read_bytes()).hexdigest() != c.SOURCE_SHA:
        raise ValueError('requires pinned core2024 fixture')
    if profile['source_sha256'] != c.SOURCE_SHA or profile['reader_revision'] != c.REV:
        raise ValueError('profile source/reader differs')
    matches = [e for e in identity_evidence if e['sha256'] == c.SOURCE_SHA]
    if len(matches) != 1:
        raise ValueError('requires unique source identity evidence')
    names = ['Global/History', 'Global/ElemTable', 'Global/DocumentIncrementTable', 'Contents', 'BasicFileInfo', 'Global/Latest', 'ProjectInformation']
    with olefile.OleFileIO(source) as f:
        stored = {n: f.openstream(n).read() for n in names}
        schema = zlib.decompress(c.unpage(f.openstream('Formats/Latest').read()), 31)
        if f.exists('Partitions/66'):
            raise ValueError('partition66 already exists')
    if hashlib.sha256(schema).hexdigest() != profile['schema_sha256']:
        raise ValueError('embedded schema profile mismatch')
    logical = {n: c.unpage(stored[n]) for n in names if n not in ('BasicFileInfo', 'ProjectInformation')}
    history = c.save_history.decode(c.unpack_global(logical[names[0]])[0])
    table = c.element_table.decode(c.unpack_global(logical[names[1]])[0], 8)
    tag, fields = c.save_increments.decode(c.unpack_global(logical[names[2]])[0])
    if len(fields['m_increments']) != 66 or history.next_sequence != 39 or table.last_id != 133209:
        raise ValueError('source allocation state differs')
    newtable = table
    for wall in walls:
        ident, newtable = c.allocate_identity(newtable, history)
        if ident != wall['id']:
            raise ValueError('unexpected allocation')
    episode = uuid.uuid5(c.EPISODE, json.dumps([w['spec'] for w in walls], sort_keys=True))
    newhistory = c.save_history.prepend_episode(history, episode.bytes_le)
    partition = c.partition_encode(c.build_partition(0x37b,
        {ch: tuple(c.Record(w['id'], w['bodies'][ch]) for w in walls) for ch in (101, 102, 103)}, 8, allow_unsigned_nonempty=True))
    revised = c.append_increment(fields, 39, 1792627200)
    for name in ('m_increments', 'm_localIncrements'):
        revised[name][-1]['m_totalElements'] = len(walls)
        revised[name][-1]['m_incrementVersions'][0]['m_totalElements'] = len(walls)
        revised[name][-1]['m_comment'] = 'Unsigned bounded multi-wall append; lifecycle hypotheses'
        revised[name][-1]['m_basicFileInfoStreamRevision'] += 1
    revised = c.advance_regular_ancillary_revisions(fields, revised)
    revisions = {n: revised['m_increments'][-1][f'm_{n}StreamRevision'] for n in c.save_increments.REVISIONS}
    evidence = registration_evidence.get('source_evidence', registration_evidence)
    registered, registration = register_batch(c.unpack_global(logical['Global/Latest'])[0], evidence, [w['id'] for w in walls])
    from project_information_codec import patch_timestamp
    project, timestamp_report = patch_timestamp(stored['ProjectInformation'], hashlib.sha256(stored['ProjectInformation']).hexdigest(), fields['m_increments'][-1]['m_atimeStamp']['m_lsb'], 1792627200)
    payloads = {
        names[0]: c.repack_global(logical[names[0]], c.save_history.encode(newhistory)),
        names[1]: c.repack_global(logical[names[1]], c.element_table.encode(newtable)),
        names[2]: c.repack_global(logical[names[2]], c.save_increments.encode(tag, revised)),
        'Contents': c.patch_contents_payload(logical['Contents'], matches[0], revisions),
        'BasicFileInfo': c.basic_file_info_codec.encode(c.basic_file_info_codec.decode(stored['BasicFileInfo']), 67, str(episode)),
        'Global/Latest': c.repack_global(logical['Global/Latest'], registered),
        'ProjectInformation': project,
    }
    plan = {'source_sha256': c.SOURCE_SHA, 'reader_revision': c.REV, 'new_element_ids': [w['id'] for w in walls],
        'new_episode': 39, 'new_episode_guid': str(episode), 'new_partition': 'Partitions/66',
        'source_rows': len(table.rows), 'new_rows': len(newtable.rows), 'prior_table_rows_byte_identical': newtable.rows[:-len(walls)] == table.rows,
        'walls': [{k: v for k, v in w.items() if k != 'bodies'} | {'body_sha256': {str(ch): hashlib.sha256(b).hexdigest() for ch, b in w['bodies'].items()}} for w in walls],
        'registration_change': registration, 'project_information_timestamp': timestamp_report,
        'partition_payload_sha256': hashlib.sha256(partition).hexdigest(),
        'autodesk_acceptance': 'not_tested', 'complete_save_transaction': False, 'production_native_export': False,
        'hypotheses': ['Unsigned partitions accepted.', 'One new episode and ordinal partition support multiple new walls.',
            'Measured structural registration and known save metadata suffice.', 'Non-room-bounding flags suppress topology lifecycle requirements; unproven.',
            'Saved source header bounds represent the needed separation domain; regenerated geometry is not proven.']}
    dest.mkdir(parents=True, exist_ok=False)
    patches = []
    for stream, payload in payloads.items():
        name = stream.replace('/', '-') + '.bin'
        (dest / name).write_bytes(payload)
        patches.append({'stream': stream, 'expected_stored_sha256': hashlib.sha256(stored[stream]).hexdigest(), 'new_payload_file': name})
    (dest / 'partition.bin').write_bytes(partition)
    (dest / 'manifest.json').write_text(json.dumps({'input_sha256': c.SOURCE_SHA, 'patches': patches,
        'creates': [{'stream': 'Partitions/66', 'expected_absent': True, 'new_payload_file': 'partition.bin'}]}, indent=2) + '\n')
    (dest / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('destination', type=Path)
    parser.add_argument('--specs', type=Path, help='JSON list; omitted uses three-wall demo')
    parser.add_argument('--acknowledge-hypotheses', action='store_true')
    args = parser.parse_args(); results = Path(__file__).parent / 'results'
    plan = make(args.source, args.destination, json.loads((results / 'wall-element-profile.json').read_bytes()),
        json.loads((results / 'save-identity.json').read_bytes()), json.loads((results / 'wall-element-registration.json').read_bytes()),
        json.loads(args.specs.read_bytes()) if args.specs else DEMO_SPECS, acknowledge_hypotheses=args.acknowledge_hypotheses)
    print(json.dumps(plan, indent=2))
