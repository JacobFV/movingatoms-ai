"""Check timestamp-only ProjectInformation patches across eleven licensed files."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import olefile
from ancillary_transitions import inflate
from codec import decode as unpage
from fetch_fixture import FILES, HOLDOUTS
from paired_save_sources import SNAPSHOTS
from project_information_codec import parse, patch_timestamp
from save_increments import decode as increments_decode


def metadata(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.infolist()[0]
        return ({key: getattr(info, key) for key in ('filename', 'date_time', 'compress_type', 'comment',
            'extra', 'create_system', 'create_version', 'extract_version', 'reserved', 'flag_bits',
            'volume', 'internal_attr', 'external_attr')}, archive.comment)


def run(directory):
    specs = {name: sha for _, name, sha in FILES}
    specs.update(dict(HOLDOUTS))
    specs.update(('core-history-'+commit[:8]+'.rvt', sha) for commit, sha, _ in SNAPSHOTS if not commit.startswith('fd755e18'))
    reports = []
    for name, expected in specs.items():
        path = directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('fixture hash mismatch')
        with olefile.OleFileIO(path) as file:
            source = file.openstream('ProjectInformation').read()
            raw, _ = inflate(unpage(file.openstream('Global/DocumentIncrementTable').read()), 8)
            latest = increments_decode(raw)[1]['m_increments'][-1]
        time = latest['m_atimeStamp']
        if time['m_msb'] != 0:
            raise ValueError('unsupported timestamp high word')
        sha = hashlib.sha256(source).hexdigest()
        unchanged, _ = patch_timestamp(source, sha, time['m_lsb'], time['m_lsb'])
        if unchanged != source:
            raise ValueError('identity patch changed ZIP')
        changed, evidence = patch_timestamp(source, sha, time['m_lsb'], time['m_lsb']+60)
        if metadata(source) != metadata(changed):
            raise ValueError('independent ZIP metadata changed')
        original_xml, old_stamp, *_ = parse(source)
        changed_xml, new_stamp, *_ = parse(changed)
        if changed_xml != original_xml.replace(old_stamp.encode('ascii'), new_stamp.encode('ascii')):
            raise ValueError('unexpected XML changes')
        reports.append({'file': name, 'sha256': expected, 'project_information_sha256': sha,
            'identity_patch_byte_exact': True, 'independent_zip_metadata_equal': True,
            'changed_zip_readable': True, 'xml_timestamp_fields_changed': 2,
            'xml_original_bytes': len(original_xml), 'xml_changed_bytes': len(changed_xml),
            **evidence})
    return {'fixtures': reports,
        'limitations': ['Preserving source-derived offset is a save-policy hypothesis.',
            'Only observed source offsets 14400 and 36000 seconds and single-entry flag-2 deflate ZIPs are supported.',
            'No paired lineage establishes daylight-saving transitions or multi-user timezone behavior.',
            'No Autodesk acceptance result.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('directory', type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2))
