"""Private-value-free ProjectInformation XML transition evidence."""
import argparse
import copy
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import olefile
from ancillary_transitions import digest, inflate
from codec import decode as unpage
from paired_save_sources import SNAPSHOTS
from save_increments import decode as increments_decode, REVISIONS
from save_history import decode as history_decode
import uuid

UPDATED_TAGS = {'{http://www.w3.org/2005/Atom}updated',
                '{urn:schemas-autodesk-com:partatom}updated'}


def leaves(root):
    result = {}
    def visit(node, path):
        if node.text and node.text.strip():
            result[path+'/#text'] = node.text
        for key, value in node.attrib.items():
            result[path+'/@'+key] = value
        counters = {}
        for child in node:
            ordinal = counters.get(child.tag, 0); counters[child.tag] = ordinal+1
            visit(child, path+'/'+child.tag+f'[{ordinal}]')
    visit(root, root.tag+'[0]')
    return result


def summary(value):
    return {'sha256': digest(value.encode('utf-8')), 'characters': len(value)}


def run(directory):
    reports = []; values = []
    for commit, expected, size in SNAPSHOTS:
        name = 'core2024.rvt' if commit.startswith('fd755e18') else 'core-history-'+commit[:8]+'.rvt'
        path = directory/name; data = path.read_bytes()
        if len(data) != size or digest(data) != expected:
            raise ValueError('fixture hash mismatch')
        with olefile.OleFileIO(path) as file:
            archive_data = file.openstream('ProjectInformation').read()
            raw, _ = inflate(unpage(file.openstream('Global/DocumentIncrementTable').read()), 8)
            increments = increments_decode(raw)[1]['m_increments']; latest = increments[-1]
            history_raw, _ = inflate(unpage(file.openstream('Global/History').read()), 8)
            history = history_decode(history_raw)
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            entries = archive.infolist()
            if len(entries) != 1:
                raise ValueError('only one project XML entry is supported')
            xml = archive.read(entries[0])
        root = ET.fromstring(xml); leaf_values = leaves(root)
        updated = [node.text for node in root.iter() if node.tag in UPDATED_TAGS]
        if len(updated) != 2 or any(value is None for value in updated):
            raise ValueError('unexpected project XML updated fields')
        timestamps = [int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()) for value in updated]
        scrubbed = copy.deepcopy(root)
        for node in scrubbed.iter():
            if node.tag in UPDATED_TAGS:
                node.text = '[TIMESTAMP]'
        normalized = ET.tostring(scrubbed, encoding='utf-8')
        expected_values = {'newest_history_episode': str(uuid.UUID(bytes_le=history.episodes[0][:16])),
                           'increment_entries': str(len(increments)),
                           'latest_major_version': str(latest['m_majorVersion'])}
        expected_values.update((n+'_revision', str(latest[f'm_{n}StreamRevision'])) for n in REVISIONS)
        matches = [{'path': key, 'field': field} for key, value in leaf_values.items()
                   for field, target in expected_values.items() if value == target]
        reports.append({'file': name, 'sha256': expected,
            'zip_entries': 1, 'zip_entry_name_sha256': digest(entries[0].filename.encode('utf-8')),
            'xml_bytes': len(xml), 'xml_sha256': digest(xml), 'root_tag': root.tag,
            'updated_element_tags': sorted(UPDATED_TAGS), 'updated_fields_equal': updated[0] == updated[1],
            'increment_timestamp_msb': latest['m_atimeStamp']['m_msb'],
            'increment_timestamp_minus_xml_updated_seconds': [latest['m_atimeStamp']['m_lsb']-t for t in timestamps],
            'xml_with_updated_values_normalized_sha256': digest(normalized),
            'leaf_count': len(leaf_values), 'identity_value_matches': matches})
        values.append(leaf_values)
    pairs = []
    for index in range(1, len(reports)):
        old, new = values[index-1:index+1]
        changed = []
        for key in sorted(old.keys()|new.keys()):
            if old.get(key) != new.get(key):
                changed.append({'path': key, 'old': summary(old[key]) if key in old else None,
                                'new': summary(new[key]) if key in new else None})
        pairs.append({'older': reports[index-1]['file'], 'newer': reports[index]['file'],
            'changed_values': changed,
            'xml_equal_after_updated_value_normalization': reports[index-1]['xml_with_updated_values_normalized_sha256'] == reports[index]['xml_with_updated_values_normalized_sha256']})
    return {'snapshots': reports, 'pairs': pairs,
            'limitations': ['The 14400-second offset is observed in this lineage; timezone and clock semantics are unproven.',
                'No general rule for generating timestamps follows from this single document lineage.',
                'ZIP entry names and private XML values are represented by hashes only.',
                'ProjectXMLInfo revision-to-ProjectInformation stream binding remains an inference.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('directory', type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2))
