"""Pinned, MIT-licensed historical Core Interior snapshots and lineage audit."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import uuid
import zlib
import olefile
from codec import decode as unpage
from save_history import decode as history_decode
from save_increments import decode as increments_decode

REPO = 'magnetar-io/revit-test-datasets'
MODEL = 'Revit/2024_Core_Interior.rvt'
LICENSE_SHA256 = '0ab138580e235fd4024d9a0d7589a9fe6982aab1503356415cdef15d1e2cb4fc'
SNAPSHOTS = [
    [
        "bd8c079268e7b109e37ff5cf9037de0877ec4a01",
        "7504e04526fa581fa76236cc0c99f2a14029cdfb6ee62be86fa75733aa1075da",
        17731584
    ],
    [
        "21b61e69b5d0552214fc2159e6d529118c6c24f1",
        "5a963a88f67ad709c232a4f7e2b94de85bd23ac73ba77903cc3ec996de1b9d28",
        23490560
    ],
    [
        "5859762b4fb07319829ad382fbad356237dec1ca",
        "108d28c14e4789cd2aadf89c4c308ff09c769ed6b30546d129dacda749bc8164",
        20779008
    ],
    [
        "ede6e635abd10a251e1d11a3603e9002898d0632",
        "8518ea433d63e1d35c136b1f6fc7588d40004efff0d73e8b71ffaca90241c37c",
        29282304
    ],
    [
        "8946a8caaf7ca00ee81d843581b91d97fdbe4c6f",
        "dd016430d9ce0a115895a81ccad6c576475914890a538322885bb80744119a69",
        30814208
    ],
    [
        "fd755e18cec40ed016d06b082f420d796571fef1",
        "c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014",
        33718272
    ]
]


DISCOVERED_HISTORY = [{'repo': 'magnetar-io/revit-test-datasets',
  'path': 'Revit/2024_Core_Interior.rvt',
  'api_url': 'https://api.github.com/repos/magnetar-io/revit-test-datasets/commits?path=Revit/2024_Core_Interior.rvt&per_page=100',
  'commits': [{'sha': 'fd755e18cec40ed016d06b082f420d796571fef1',
               'date': '2024-06-02T17:15:46Z',
               'message': 'added curtain wal and wall sample.'},
              {'sha': '8946a8caaf7ca00ee81d843581b91d97fdbe4c6f',
               'date': '2023-08-13T14:42:13Z',
               'message': 'Updated Demo view and Properties'},
              {'sha': 'ede6e635abd10a251e1d11a3603e9002898d0632',
               'date': '2023-08-12T23:36:19Z',
               'message': 'Updated Rhino\n'
                          '\n'
                          'I added the objects the layers, added materials and colors and added a '
                          'custom "Classification" value.  Plate or Mullion'},
              {'sha': '5859762b4fb07319829ad382fbad356237dec1ca',
               'date': '2023-08-06T14:18:12Z',
               'message': 'Update 2024_Core_Interior.rvt'},
              {'sha': '21b61e69b5d0552214fc2159e6d529118c6c24f1',
               'date': '2023-08-06T14:02:46Z',
               'message': 'Add Rhino Facade'},
              {'sha': 'bd8c079268e7b109e37ff5cf9037de0877ec4a01',
               'date': '2023-08-06T13:45:57Z',
               'message': 'CleanedUP'}]},
 {'repo': 'magnetar-io/revit-test-datasets',
  'path': 'Revit/Revit_IFC5_Einhoven.rvt',
  'api_url': 'https://api.github.com/repos/magnetar-io/revit-test-datasets/commits?path=Revit/Revit_IFC5_Einhoven.rvt&per_page=100',
  'commits': [{'sha': 'fd755e18cec40ed016d06b082f420d796571fef1',
               'date': '2024-06-02T17:15:46Z',
               'message': 'added curtain wal and wall sample.'}]},
 {'repo': 'Drshelden/IFC-ECS',
  'path': 'data/RE1/RE1-Architecture.rvt',
  'api_url': 'https://api.github.com/repos/Drshelden/IFC-ECS/commits?path=data/RE1/RE1-Architecture.rvt&per_page=100',
  'commits': [{'sha': 'c5a9ecffbd93dc6900cf351686656f0736230e88',
               'date': '2026-02-17T01:24:21Z',
               'message': 'with repaired tree'}]},
 {'repo': 'Drshelden/IFC-ECS',
  'path': 'data/RE1/RE1-Electrical.rvt',
  'api_url': 'https://api.github.com/repos/Drshelden/IFC-ECS/commits?path=data/RE1/RE1-Electrical.rvt&per_page=100',
  'commits': [{'sha': 'c5a9ecffbd93dc6900cf351686656f0736230e88',
               'date': '2026-02-17T01:24:21Z',
               'message': 'with repaired tree'}]},
 {'repo': 'Drshelden/IFC-ECS',
  'path': 'data/RE1/RE1-Mechanical.rvt',
  'api_url': 'https://api.github.com/repos/Drshelden/IFC-ECS/commits?path=data/RE1/RE1-Mechanical.rvt&per_page=100',
  'commits': [{'sha': 'c5a9ecffbd93dc6900cf351686656f0736230e88',
               'date': '2026-02-17T01:24:21Z',
               'message': 'with repaired tree'}]},
 {'repo': 'Drshelden/IFC-ECS',
  'path': 'data/RE1/RE1-Plumbing.rvt',
  'api_url': 'https://api.github.com/repos/Drshelden/IFC-ECS/commits?path=data/RE1/RE1-Plumbing.rvt&per_page=100',
  'commits': [{'sha': 'c5a9ecffbd93dc6900cf351686656f0736230e88',
               'date': '2026-02-17T01:24:21Z',
               'message': 'with repaired tree'}]}]

def read_global(file, name, decoder):
    stored = file.openstream('Global/'+name).read()
    report = {'stored_sha256': hashlib.sha256(stored).hexdigest(), 'stored_bytes': len(stored)}
    try:
        logical = unpage(stored)
        d = zlib.decompressobj(31); raw = d.decompress(logical[8:])
        if not d.eof or d.unconsumed_tail:
            raise ValueError('incomplete gzip')
        value = decoder(raw)
        report.update(status='decoded', inflated_sha256=hashlib.sha256(raw).hexdigest(),
                      opaque_logical_gzip_suffix_bytes=len(d.unused_data))
        return value, report
    except ValueError as error:
        report.update(status='unsupported', error=str(error))
        return None, report


def run(directory, fetch=False):
    reports = []; histories = []
    for commit, expected, size in SNAPSHOTS:
        name = 'core2024.rvt' if commit.startswith('fd755e18') else 'core-history-'+commit[:8]+'.rvt'
        path = directory/name
        license_url = f'https://raw.githubusercontent.com/{REPO}/{commit}/LICENSE'
        model_url = f'https://media.githubusercontent.com/media/{REPO}/{commit}/{MODEL}'
        if fetch:
            license_data = urllib.request.urlopen(license_url, timeout=30).read()
            if hashlib.sha256(license_data).hexdigest() != LICENSE_SHA256:
                raise ValueError('historical MIT license changed')
            if not path.exists():
                data = urllib.request.urlopen(model_url, timeout=60).read()
                if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError('historical model hash mismatch')
                path.write_bytes(data)
        data = path.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('historical model hash mismatch')
        with olefile.OleFileIO(path) as file:
            history, history_report = read_global(file, 'History', history_decode)
            increments, increment_report = read_global(file, 'DocumentIncrementTable', increments_decode)
        report = {'file': name, 'repo': REPO, 'commit': commit, 'sha256': expected, 'size': size,
            'model_url': model_url, 'license_url': license_url,
            'license_sha256': LICENSE_SHA256, 'license': 'MIT',
            'history': history_report, 'increments': increment_report}
        if history:
            report['history'].update(episodes=len(history.episodes),
                newest_episode_guid=str(uuid.UUID(bytes_le=history.episodes[0][:16])),
                creation_guid=str(uuid.UUID(bytes_le=history.guids[0])))
        if increments:
            rows = increments[1]['m_increments']
            report['increments'].update(entries=len(rows), latest_major_version=rows[-1]['m_majorVersion'])
        reports.append(report); histories.append(history)
    pairs = []
    for i in range(1, len(reports)):
        old, new = histories[i-1:i+1]
        pair = {'older': reports[i-1]['file'], 'newer': reports[i]['file']}
        if old is None or new is None:
            pair['status'] = 'blocked_by_strict_page_decoder'
        else:
            pair.update(status='history_lineage_checked',
                same_creation_guid=old.guids[0] == new.guids[0],
                newer_preserves_all_older_episodes_as_suffix=new.episodes[-len(old.episodes):] == old.episodes,
                older_episodes=len(old.episodes), newer_episodes=len(new.episodes),
                episode_delta=len(new.episodes)-len(old.episodes),
                different_newest_episode=old.episodes[0] != new.episodes[0])
        pairs.append(pair)
    return {'repo_history_api': f'https://api.github.com/repos/{REPO}/commits?path={MODEL}&per_page=100',
        'discovered_path_history': DISCOVERED_HISTORY,
        'initial_transport_counterexamples': [
            {'file': 'core-history-8946a8ca.rvt', 'stream': 'Global/History', 'stored_bytes': 797,
             'initial_error': 'invalid, ambiguous, or unsupported final-page framing',
             'cause': 'unique valid historical layout was excluded by canonical layout selection'},
            {'file': 'core-history-ede6e635.rvt', 'stream': 'Global/DocumentIncrementTable', 'stored_bytes': 1772,
             'initial_error': 'invalid, ambiguous, or unsupported final-page framing',
             'cause': 'unique valid historical layout was excluded by canonical layout selection'}],
        'snapshots': reports, 'adjacent_git_snapshot_pairs': pairs,
        'limitations': ['Git-adjacent snapshots need not be adjacent Revit saves.',
            'Shared creation GUID and preserved episode history establish file lineage, not the exact user operation.',
            'Unsupported page framing is reported; no unchecked transport fallback is used.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--fetch', action='store_true')
    a = p.parse_args()
    print(json.dumps(run(a.directory, a.fetch), indent=2))
