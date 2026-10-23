"""Build and independently verify a minimal-seed native wall research candidate.

Only publish the candidate after transport and saved-file checks bind its bytes.
Publication establishes the recorded local checks, never native application acceptance.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from wall_batch_experiment import code_snapshot, digest, publish_checked, write_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def run(source, destination, specs, reader, target, writer, ifc_python, *, acknowledge_hypotheses=False):
    from seed_wall_candidate import make, checked_specs
    if not acknowledge_hypotheses:
        raise ValueError('explicit experimental seed/save hypotheses acknowledgment required')
    specs = checked_specs(specs)
    source, destination, reader, target, writer = (p.resolve() for p in (source, destination, reader, target, writer))
    ifc_python = ifc_python.absolute()
    for path in (source, writer, ifc_python, reader / 'Cargo.toml'):
        if not path.is_file():
            raise ValueError(f'missing required input/tool: {path}')
    if destination.exists():
        raise FileExistsError(destination)
    subprocess.run([str(ifc_python), '-c', 'import ifcopenshell; assert ifcopenshell.version == "0.8.5"'], check=True)
    results = HERE / 'results'
    names = ('wall-element-profile.json', 'seed_level-profile.json', 'seed_save_context.json', 'seed_wall_context.json')
    profile_bytes = {name: (results / name).read_bytes() for name in names}
    profiles = [json.loads(profile_bytes[name]) for name in names]
    code = code_snapshot()
    destination.mkdir(parents=True, exist_ok=False)
    staging = destination / 'staging'
    staging.mkdir()
    report = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
              'source_sha256': digest(source), 'request': specs, 'checks': [],
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': code, 'writer_sha256': digest(writer),
              'profile_sha256': {name: digest(results / name) for name in names},
              'autodesk_acceptance': 'not_tested', 'production_native_export': False}
    report_path = destination / 'run.json'
    write_json(report_path, report)

    def phase(name, command):
        with (destination / (name + '.stdout.log')).open('wb') as out, (destination / (name + '.stderr.log')).open('wb') as err:
            completed = subprocess.run([str(v) for v in command], cwd=ROOT, stdout=out, stderr=err)
        report['checks'].append({'name': name, 'exit_code': completed.returncode})
        write_json(report_path, report)
        if completed.returncode:
            raise RuntimeError(f'{name} failed; see {destination / (name + ".stderr.log")}')

    try:
        plan = make(source, staging / 'patches', *profiles, specs, acknowledge_hypotheses=True)
        plan_path = staging / 'patches/plan.json'
        write_json(destination / 'request.json', specs)
        candidate = staging / 'candidate.rvt'
        phase('writer', [writer, 'patch', source, candidate, staging / 'patches/manifest.json'])
        phase('transport', [writer, 'verify', candidate])
        metadata_path = destination / 'metadata.json'
        phase('metadata', [sys.executable, HERE / 'seed_metadata_audit.py', source, candidate, '--result', metadata_path])
        native_path = destination / 'native.json'
        phase('native', [sys.executable, HERE / 'seed_wall_verify.py', '--source', source, '--candidate', candidate,
                         '--plan', plan_path, '--reader', reader, '--target', target, '--output', native_path])
        # Native verification exports the actual saved candidate through the
        # independent public reader. IFC geometry is checked in its pinned environment.
        ifc_path = destination / 'ifc.json'
        phase('ifc', [ifc_python, HERE / 'seed_wall_verify.py', '--ifc-report', native_path, '--output', ifc_path])
        if code_snapshot() != code or digest(source) != report['source_sha256'] or digest(writer) != report['writer_sha256']:
            raise RuntimeError('research code, source or writer changed during verification')
        if any((results / name).read_bytes() != raw for name, raw in profile_bytes.items()):
            raise RuntimeError('source evidence changed during verification')
        checks = [json.loads(path.read_bytes()) for path in (metadata_path, native_path, ifc_path)]
        candidate_sha = publish_checked(candidate, destination / 'verified-candidate.rvt', checks)
        report.update(status='verified_research_candidate', candidate_sha256=candidate_sha,
                      new_element_ids=plan['expected_new_ids'], candidate_file='verified-candidate.rvt',
                      validation_reports={p.name: digest(p) for p in (metadata_path, native_path, ifc_path)},
                      completed_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(report_path, report)
        return report
    except Exception as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}', completed_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(report_path, report)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--specs', type=Path, required=True)
    parser.add_argument('--reader-source', type=Path, required=True)
    parser.add_argument('--target', type=Path, default=HERE / 'local/seed-wall-verify-build')
    parser.add_argument('--writer', type=Path, default=ROOT / 'processing/rvt-native/target/release/ma-rvt-native')
    parser.add_argument('--ifc-python', type=Path, default=HERE / 'local/ifc-validation-env/bin/python')
    parser.add_argument('--acknowledge-hypotheses', action='store_true')
    args = parser.parse_args()
    report = run(args.source, args.destination, json.loads(args.specs.read_bytes()), args.reader_source,
                 args.target, args.writer, args.ifc_python, acknowledge_hypotheses=args.acknowledge_hypotheses)
    print(json.dumps({k: report[k] for k in ('status', 'candidate_sha256', 'new_element_ids')}, indent=2))
