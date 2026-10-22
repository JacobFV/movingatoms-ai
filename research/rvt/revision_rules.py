"""Reproduce observed revision relationships without prescribing save semantics.

Historical rows are retained metadata, not paired historical stream snapshots.
A passing relationship is a corpus observation, never an Autodesk contract.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zlib

import olefile
from codec import decode as unpage
from save_increments import decode, encode, REVISIONS
from save_history import decode as history_decode
from schema_probe import REV


def analyze(rows, history_count):
    if not rows:
        raise ValueError('empty increment sequence')
    def revision(row, name):
        return row[f'm_{name}StreamRevision']
    checks = {
        'major_version_equals_ordinal_plus_one': lambda i, r: r['m_majorVersion'] == i+1,
        'total_episodes_equals_greatest_plus_one': lambda i, r: r['m_totalEpisodes'] == r['m_greatest']['m_id']+1,
        'episode_count_within_current_history': lambda i, r: 0 <= r['m_totalEpisodes'] <= history_count,
        'history_equals_global': lambda i, r: revision(r, 'history') == revision(r, 'global'),
        'element_table_equals_global': lambda i, r: revision(r, 'elemTable') == revision(r, 'global'),
        'partition_table_equals_global': lambda i, r: revision(r, 'partitionTable') == revision(r, 'global'),
        'global_equals_ordinal': lambda i, r: revision(r, 'global') == i,
        'increment_table_equals_global': lambda i, r: revision(r, 'incrementTable') == revision(r, 'global'),
        'all_stream_revisions_equal_global': lambda i, r: all(revision(r, n) == revision(r, 'global') for n in REVISIONS),
    }
    observations = {}
    for name, check in checks.items():
        failures = [i for i, row in enumerate(rows) if not check(i, row)]
        observations[name] = {'checked': len(rows), 'counterexample_ordinals': failures,
                              'holds_in_this_file': not failures}
    fields = {}
    for name in REVISIONS:
        values = [revision(r, name) for r in rows]
        fields[name] = {'first': values[0], 'latest': values[-1],
            'step_histogram': dict(sorted(Counter(b-a for a, b in zip(values, values[1:])).items())),
            'decreasing_at_ordinals': [i for i in range(1, len(values)) if values[i] < values[i-1]],
            'offsets_from_global': sorted({value-revision(row, 'global') for value, row in zip(values, rows)})}
    return {'entries': len(rows), 'history_episodes': history_count,
        'latest_total_episodes_equals_history_count': rows[-1]['m_totalEpisodes'] == history_count,
        'global_minus_ordinal_values': sorted({revision(r, 'global')-i for i, r in enumerate(rows)}),
        'fields': fields, 'relationships': observations,
        'latest': {**{n: revision(rows[-1], n) for n in REVISIONS},
                   'major_version': rows[-1]['m_majorVersion'],
                   'greatest_episode': rows[-1]['m_greatest']['m_id'],
                   'total_episodes': rows[-1]['m_totalEpisodes']}}


def inflate(stream):
    logical = unpage(stream)
    d = zlib.decompressobj(31)
    raw = d.decompress(logical[8:])
    if not d.eof or d.unconsumed_tail:
        raise ValueError('incomplete global gzip')
    return raw


def audit(evidence, directory):
    reports = []
    for item in evidence:
        path = directory/item['file']
        if path.parent.resolve() != directory.resolve():
            raise ValueError('unsafe fixture name')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256'] or item['reader_commit'] != REV:
            raise ValueError('fixture or reader evidence mismatch')
        with olefile.OleFileIO(path) as source:
            raw = inflate(source.openstream('Global/DocumentIncrementTable').read())
            history = history_decode(inflate(source.openstream('Global/History').read()))
        tag, fields = decode(raw)
        if fields != item['increment_root']['fields'] or tag != item['increment_root']['class_tag']:
            raise ValueError('independent schema decoder differs')
        if encode(tag, fields) != raw:
            raise ValueError('increment roundtrip differs')
        reports.append({'file': path.name, 'sha256': digest, 'reader_commit': REV,
            'increment_payload_sha256': hashlib.sha256(raw).hexdigest(),
            'independent_schema_agrees': True,
            'arrays_equal': fields['m_increments'] == fields['m_localIncrements'],
            'increments': analyze(fields['m_increments'], len(history.episodes)),
            'local_increments': analyze(fields['m_localIncrements'], len(history.episodes))})
    return {'status': 'observed_relationships_only',
        'save_rules_established': False,
        'limitations': ['No before/after save pair is available.',
            'A revision change cannot be equated with stream byte change from historical metadata alone.',
            'An append candidate must label revision extrapolation as a hypothesis.',
            'Monotonicity and equality do not establish how overwrite, upgrade or compaction allocate revisions.'],
        'fixtures': reports}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path)
    p.add_argument('directory', type=Path)
    a = p.parse_args()
    print(json.dumps(audit(json.loads(a.evidence.read_bytes()), a.directory), indent=2))
