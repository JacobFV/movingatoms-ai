"""Collect local Cargo and Rust license evidence without choosing SPDX alternatives.

This is a file/provenance inventory, not a legal compatibility determination.
Only explicitly excluded first-party package roots may omit license evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

PREFIXES = ('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'UNLICENSE', 'COPYRIGHT')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(path):
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('license evidence symlink forbidden: ' + str(path))
    return path


def evidence_files(root, explicit=None):
    root = checked_path(root)
    selected = set()
    # Do not follow symlinks, including symlink directories hiding notices.
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ('.git', 'target')]
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError('license evidence symlink forbidden: ' + str(path))
        for name in files:
            if name.upper().startswith(PREFIXES):
                selected.add(Path(directory) / name)
    if explicit:
        path = checked_path(root / explicit)
        if not path.is_relative_to(root):
            raise ValueError('license_file escapes package root')
        selected.add(path)
    result = []
    for path in sorted(selected):
        if not path.is_file() or not path.read_bytes().strip():
            raise ValueError('missing or empty license evidence: ' + str(path))
        result.append(path)
    if not result:
        raise ValueError('missing third-party license evidence: ' + str(root))
    return result


def collect_metadata_licenses(metadatas, *, excluded_roots=()):
    """Pure collection from host-filtered metadata; useful for deterministic tests.

    Exclusions are exact manifest directories, never package-name wildcards.
    Same name/version from distinct sources is rejected instead of overwriting.
    """
    excluded = {str(checked_path(p)) for p in excluded_roots}
    payloads, records, seen, excluded_records = {}, [], {}, []
    for metadata in metadatas:
        packages = {p['id']: p for p in metadata['packages']}
        if len(packages) != len(metadata['packages']):
            raise ValueError('duplicate package IDs')
        resolve = metadata['resolve']
        if not resolve or not resolve.get('root'):
            raise ValueError('resolved package root required')
        nodes = {n['id']: n for n in resolve['nodes']}
        pending, reachable = [resolve['root']], set()
        while pending:
            identity = pending.pop()
            if identity in reachable:
                continue
            if identity not in nodes or identity not in packages:
                raise ValueError('unresolved package in license graph')
            reachable.add(identity)
            pending.extend(nodes[identity]['dependencies'])
        for identity in sorted(reachable):
            p = packages[identity]
            root = checked_path(p['manifest_path']).parent
            if str(root) in excluded:
                entry = {'package_id': identity, 'name': p['name'], 'version': p['version'],
                         'reason': 'explicit first-party package root exclusion'}
                if entry not in excluded_records:
                    excluded_records.append(entry)
                continue
            name, version = p['name'], p['version']
            if not all(isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9_.+\-]+', v) for v in (name, version)):
                raise ValueError('unsafe package name/version')
            key = name + '-' + version
            provenance = (identity, str(root), p.get('source'), p.get('license'), p.get('license_file'))
            if key in seen:
                if seen[key] != provenance:
                    raise ValueError('package name/version collision: ' + key)
                continue
            seen[key] = provenance
            files = evidence_files(root, p.get('license_file'))
            # A NOTICE alone is not adequate license text evidence.
            if not any(f.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'UNLICENSE'))
                       or (p.get('license_file') and f == root / p['license_file']) for f in files):
                raise ValueError('missing third-party license text: ' + key)
            record = {'package_id': identity, 'name': name, 'version': version,
                      'source': p.get('source'), 'declared_license': p.get('license'),
                      'license_file': p.get('license_file'), 'files': []}
            for path in files:
                relative = path.relative_to(root).as_posix()
                target = 'notices/rust-dependencies/' + key + '/' + relative
                raw = path.read_bytes()
                if target in payloads:
                    raise ValueError('license payload collision')
                payloads[target] = raw
                record['files'].append({'package_path': relative, 'path': target,
                                        'sha256': sha(raw), 'bytes': len(raw)})
            records.append(record)
    return payloads, {'packages': sorted(records, key=lambda p: (p['name'], p['version'])),
                      'excluded_packages': sorted(excluded_records, key=lambda p: p['package_id'])}


def collect_toolchain_licenses(sysroot, rustc_version):
    root = checked_path(sysroot) / 'share/doc/rust'
    required = [root / 'COPYRIGHT-library.html', root / 'COPYRIGHT.html']
    license_dir = checked_path(root / 'licenses')
    gaps = [str(p) for p in required if not p.is_file()]
    if not license_dir.is_dir():
        gaps.append(str(license_dir))
    paths = [p for p in required if p.is_file()]
    if license_dir.is_dir():
        for directory, dirs, files in os.walk(license_dir, followlinks=False):
            for name in dirs + files:
                checked_path(Path(directory) / name)
            paths.extend(Path(directory) / name for name in files)
    payloads, records = {}, []
    for path in sorted(paths):
        path = checked_path(path)
        raw = path.read_bytes()
        if not raw.strip():
            raise ValueError('empty toolchain license evidence')
        target = 'notices/rust-toolchain/' + path.relative_to(root).as_posix()
        payloads[target] = raw
        records.append({'path': target, 'sha256': sha(raw), 'bytes': len(raw)})
    return payloads, {'rustc_version': rustc_version, 'scope': 'installed toolchain and standard-library copyright inventories; includes all supplied license alternatives',
                      'files': records, 'missing_evidence': gaps}


def collect_runtime_licenses(manifests, *, excluded_roots=()):
    version = subprocess.check_output(['rustc', '-vV'], text=True)
    matches = re.findall(r'^host: (\S+)$', version, re.M)
    if len(matches) != 1:
        raise ValueError('cannot determine actual Rust host triple')
    host = matches[0]
    metadata = []
    for manifest in manifests:
        metadata.append(json.loads(subprocess.check_output([
            'cargo', 'metadata', '--offline', '--locked', '--filter-platform', host,
            '--format-version', '1', '--manifest-path', str(manifest)], text=True)))
    payloads, report = collect_metadata_licenses(metadata, excluded_roots=excluded_roots)
    sysroot = subprocess.check_output(['rustc', '--print', 'sysroot'], text=True).strip()
    tool_payloads, tool_report = collect_toolchain_licenses(sysroot, version)
    payloads.update(tool_payloads)
    report.update({'host_triple': host, 'toolchain': tool_report,
                   'selection': 'resolved dependency graph from each explicit root, host-filtered Cargo metadata; includes build/proc-macro dependencies',
                   'spdx_policy': 'preserve declared expressions and all actual notices; no alternative selection or inferred license texts'})
    return payloads, report
