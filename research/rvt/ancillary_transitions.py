"""Correlate retained stream revisions with actual paired stream byte changes.

Stream-name mapping for projectXMLInfo is a documented inference from the
ProjectInformation XML container, not a proven native field binding.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib
import olefile
from codec import decode as unpage
from pages import is_paged
from paired_save_sources import SNAPSHOTS
from save_increments import decode as increments_decode, REVISIONS
from partition_segments import decode as partition_decode

STREAMS = {
    'preview': 'RevitPreview4.0', 'global': 'Global/Latest', 'history': 'Global/History',
    'elemTable': 'Global/ElemTable', 'contentDocuments': 'Global/ContentDocuments',
    'partitionTable': 'Global/PartitionTable', 'incrementTable': 'Global/DocumentIncrementTable',
    'formats': 'Formats/Latest', 'basicFileInfo': 'BasicFileInfo',
    'transmissionData': 'TransmissionData', 'partAtom': 'PartAtom',
    'projectXMLInfo': 'ProjectInformation'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inflate(data, start):
    d = zlib.decompressobj(31); raw = d.decompress(data[start:])
    if not d.eof or d.unconsumed_tail:
        raise ValueError('incomplete gzip')
    return raw, d.unused_data


def framed_digest(blobs):
    h = hashlib.sha256()
    for blob in blobs:
        h.update(struct.pack('<Q', len(blob))); h.update(blob)
    return h.hexdigest()


def fingerprint(parts, stored):
    paged = is_paged(parts)
    logical = unpage(stored) if paged else stored
    result = {'stored_bytes': len(stored), 'stored_sha256': digest(stored),
              'paged': paged, 'logical_bytes': len(logical), 'logical_sha256': digest(logical)}
    name = '/'.join(parts)
    if parts[0] == 'Partitions':
        partition = partition_decode(logical)
        bodies = [member.inflate() for segment in partition.segments for member in segment.members]
        result.update(inflation='partition_gzip_members', gzip_members=len(bodies),
                      inflated_sha256=framed_digest(bodies), inflated_bytes=sum(map(len, bodies)))
    elif parts[0] == 'Global' or name == 'Formats/Latest' or name == 'Contents':
        offset = 0 if parts[0] == 'Formats' else logical.index(b'\x1f\x8b\x08') if name == 'Contents' else 8
        raw, suffix = inflate(logical, offset)
        result.update(inflation='single_gzip', gzip_offset=offset, inflated_bytes=len(raw),
                      inflated_sha256=digest(raw), gzip_suffix_bytes=len(suffix),
                      gzip_suffix_sha256=digest(suffix))
    elif name == 'ProjectInformation':
        with zipfile.ZipFile(io.BytesIO(logical)) as archive:
            entries = archive.infolist()
            if any(e.is_dir() for e in entries):
                raise ValueError('unexpected project metadata ZIP directory')
            bodies = [archive.read(e) for e in entries]
        result.update(inflation='zip_entries_in_stored_order', zip_entries=len(bodies),
                      inflated_sha256=framed_digest(bodies), inflated_bytes=sum(map(len, bodies)),
                      zip_entry_name_hashes=[digest(e.filename.encode('utf-8')) for e in entries],
                      entry_has_xml_declaration=[b.lstrip().startswith(b'<?xml') for b in bodies])
    else:
        result['inflation'] = 'not_applied'
    return result


def run(directory):
    snapshots = []
    for commit, expected, size in SNAPSHOTS:
        name = 'core2024.rvt' if commit.startswith('fd755e18') else 'core-history-'+commit[:8]+'.rvt'
        path = directory/name; data = path.read_bytes()
        if len(data) != size or digest(data) != expected:
            raise ValueError('fixture hash mismatch')
        with olefile.OleFileIO(path) as file:
            streams = {'/'.join(parts): fingerprint(parts, file.openstream(parts).read()) for parts in file.listdir()}
            raw, _ = inflate(unpage(file.openstream('Global/DocumentIncrementTable').read()), 8)
            rows = increments_decode(raw)[1]['m_increments']
        snapshots.append({'file': name, 'sha256': expected, 'increment_entries': len(rows),
            'latest_revisions': {n: rows[-1][f'm_{n}StreamRevision'] for n in REVISIONS}, 'streams': streams})
    pairs = []
    for old, new in zip(snapshots, snapshots[1:]):
        comparisons = []
        for field, stream in STREAMS.items():
            a, b = old['streams'].get(stream), new['streams'].get(stream)
            comparison = {'revision_field': field, 'stream': stream,
                'mapping_status': 'inferred_from_project_xml_container' if field == 'projectXMLInfo' else 'name_correspondence',
                'old_revision': old['latest_revisions'][field], 'new_revision': new['latest_revisions'][field],
                'revision_delta': new['latest_revisions'][field]-old['latest_revisions'][field],
                'present_before': a is not None, 'present_after': b is not None}
            if a is not None and b is not None:
                for layer in ('stored', 'logical', 'inflated'):
                    key = layer+'_sha256'
                    if key in a and key in b:
                        comparison[layer+'_equal'] = a[key] == b[key]
                comparison['revision_advanced_with_identical_logical_bytes'] = comparison['revision_delta'] > 0 and comparison['logical_equal']
                comparison['revision_advanced_with_identical_inflated_bytes'] = comparison['revision_delta'] > 0 and comparison.get('inflated_equal') is True
            comparisons.append(comparison)
        pairs.append({'older': old['file'], 'newer': new['file'], 'streams': comparisons,
                      'added_streams': sorted(new['streams'].keys()-old['streams'].keys()),
                      'removed_streams': sorted(old['streams'].keys()-new['streams'].keys())})
    return {'status': 'paired_byte_and_revision_observations', 'snapshots': snapshots, 'pairs': pairs,
        'limitations': ['Not every Git snapshot is an adjacent Revit save.',
            'ProjectXMLInfo mapping is inferred from the uniquely named project XML ZIP; no serialized name binding is proven.',
            'Equal inflated bodies do not imply equal wrapper or gzip suffix bytes; these are separately fingerprinted.',
            'Observed revision changes do not establish a universal allocation rule.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('directory', type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2))
