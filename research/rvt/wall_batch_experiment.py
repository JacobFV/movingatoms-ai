"""Build and independently check a bounded multi-wall RVT research artifact.

A candidate is published as verified-candidate.rvt only after all checks pass.
'Verified' refers to the recorded local checks, never Autodesk acceptance.
Failed runs retain logs and staging files, clearly marked failed in run.json.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_snapshot():
    paths = list(HERE.glob('*.py')) + list(HERE.glob('*.rs'))
    crate = ROOT / 'processing/rvt-native'
    paths += list((crate / 'src').rglob('*.rs')) + [crate / 'Cargo.toml', crate / 'Cargo.lock']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def publish_checked(staged, published, checks):
    """No-clobber publication after checks bind the exact same candidate bytes."""
    actual = digest(staged)
    if not checks or any(report.get('candidate_sha256') != actual for report in checks):
        raise ValueError('all validation reports must bind the staged candidate')
    os.link(staged, published)  # Fails if published already exists; no replacement.
    return actual


def run(source, destination, specs, reader, target, writer, ifc_python, *, acknowledge_hypotheses=False):
    from wall_batch_candidate import make, validate_specs
    if not acknowledge_hypotheses:
        raise ValueError('explicit acknowledgment of experimental native save hypotheses required')
    specs = validate_specs(specs)
    source, destination, reader, target, writer = (
        p.resolve() for p in (source, destination, reader, target, writer))
    ifc_python = ifc_python.absolute()  # Preserve venv interpreter symlink path.
    for path in (source, writer, ifc_python, reader / 'Cargo.toml'):
        if not path.is_file():
            raise ValueError(f'missing required input/tool: {path}')
    if destination.exists():
        raise FileExistsError(destination)
    # Resolve imports/dependencies before reserving a run directory.
    subprocess.run([str(ifc_python), '-c', 'import ifcopenshell; assert ifcopenshell.version == "0.8.5"'], check=True)
    code = code_snapshot()
    destination.mkdir(parents=True, exist_ok=False)
    staging = destination / 'staging'; staging.mkdir()
    report = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
              'source_sha256': digest(source), 'request': specs, 'checks': [],
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': code, 'writer_sha256': digest(writer),
              'autodesk_acceptance': 'not_tested', 'production_native_export': False}
    report_path = destination / 'run.json'
    write_json(report_path, report)

    def phase(name, command):
        with (destination / (name + '.stdout.log')).open('wb') as out, (destination / (name + '.stderr.log')).open('wb') as err:
            result = subprocess.run([str(v) for v in command], cwd=ROOT, stdout=out, stderr=err)
        report['checks'].append({'name': name, 'exit_code': result.returncode})
        write_json(report_path, report)
        if result.returncode:
            raise RuntimeError(f'{name} failed; see {destination / (name + ".stderr.log")}')

    try:
        results = HERE / 'results'
        plan = make(source, staging / 'patches',
                    json.loads((results / 'wall-element-profile.json').read_bytes()),
                    json.loads((results / 'save-identity.json').read_bytes()),
                    json.loads((results / 'wall-element-registration.json').read_bytes()),
                    specs, acknowledge_hypotheses=True)
        plan_path = staging / 'patches/plan.json'
        write_json(destination / 'request.json', specs)
        candidate = staging / 'candidate.rvt'
        phase('writer', [writer, 'patch', source, candidate, staging / 'patches/manifest.json'])
        metadata_path = destination / 'metadata.json'
        phase('metadata', [sys.executable, HERE / 'wall_batch_metadata_audit.py', source, candidate, plan_path, '--result', metadata_path])
        native_path = destination / 'native.json'
        phase('native', [sys.executable, HERE / 'wall_batch_verify.py', '--reader-source', reader, '--target', target,
                         source, candidate, '--plan', plan_path, '--result', native_path])
        ifc_path = destination / 'ifc.json'
        phase('ifc', [ifc_python, HERE / 'wall_batch_verify.py', '--ifc', staging / 'candidate-source.ifc',
                      staging / 'candidate-candidate.ifc', '--native-report', native_path,
                      '--result', ifc_path, '--mesh-result', destination / 'meshes.json'])
        if code_snapshot() != code or digest(writer) != report['writer_sha256'] or digest(source) != report['source_sha256']:
            raise RuntimeError('research code changed during verification; rerun against stable files')
        metadata = json.loads(metadata_path.read_bytes()); native = json.loads(native_path.read_bytes())
        ifc = json.loads(ifc_path.read_bytes())
        # The IFC report binds its inputs to the native exporter report; require
        # the same candidate binding before publishing the native artifact.
        candidate_sha = publish_checked(candidate, destination / 'verified-candidate.rvt', [metadata, native, ifc])
        report.update(status='verified_research_candidate', candidate_sha256=candidate_sha,
                      new_element_ids=plan['new_element_ids'], candidate_file='verified-candidate.rvt',
                      validation_reports={p.name: digest(p) for p in (metadata_path, native_path, ifc_path)},
                      completed_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(report_path, report)
        return report
    except Exception as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}',
                      completed_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(report_path, report)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('destination', type=Path)
    parser.add_argument('--specs', type=Path, required=True)
    parser.add_argument('--reader-source', type=Path, required=True)
    parser.add_argument('--target', type=Path, default=HERE / 'local/batch-reader-target')
    parser.add_argument('--writer', type=Path, default=ROOT / 'processing/rvt-native/target/release/ma-rvt-native')
    parser.add_argument('--ifc-python', type=Path, default=HERE / 'local/ifc-validation-env/bin/python')
    parser.add_argument('--acknowledge-hypotheses', action='store_true')
    args = parser.parse_args()
    result = run(args.source, args.destination, json.loads(args.specs.read_bytes()), args.reader_source,
                 args.target, args.writer, args.ifc_python, acknowledge_hypotheses=args.acknowledge_hypotheses)
    print(json.dumps({'status': result['status'], 'candidate_sha256': result['candidate_sha256'],
                      'new_element_ids': result['new_element_ids']}, indent=2))
