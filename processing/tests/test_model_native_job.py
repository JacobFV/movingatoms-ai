"""Explicit worker native opt-in stages every artifact before uploads."""
import hashlib
import json
from pathlib import Path

import pytest

from ma_proc.model import build, rvt_export
from test_model import room
from test_model_jobs import FakeApi, PID


def ordinary_files(*args, **kwargs):
    return {'model.glb': b'glb', 'model.ifc': b'ifc', 'graph.json': b'{}', 'index.json': b'{}'}


def prepare(monkeypatch, tmp_path, failure=None):
    monkeypatch.setattr(build, 'build_files', ordinary_files)
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    (bundle / 'run.py').write_text('# fake runtime')
    monkeypatch.setenv('MA_RVT_RUNTIME_BUNDLE', str(bundle))
    calls = []

    def export(read, actual_bundle, output, **kwargs):
        calls.append((read, actual_bundle, kwargs))
        assert actual_bundle == bundle
        assert kwargs['acknowledge_hypotheses'] is True
        assert callable(kwargs['load_mesh'])
        if failure == 'writer':
            raise RuntimeError('writer failed')
        if failure == 'audit':
            raise ValueError('independent audit failed')
        output.mkdir()
        data = b'candidate'
        candidate = output / 'verified-candidate.rvt'
        candidate.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        reports = {}
        for name in ('transport.json', 'metadata.json', 'native.json'):
            content = json.dumps({'candidate_sha256': digest, 'check': name}).encode()
            (output / name).write_bytes(content)
            reports[name] = hashlib.sha256(content).hexdigest()
        report = {'status': 'verified_research_candidate', 'candidate_sha256': digest,
                  'production_native_export': False, 'autodesk_acceptance': 'not_tested', 'validation_reports': reports}
        if failure == 'qualification':
            report['production_native_export'] = True
        if failure == 'evidence':
            (output / 'native.json').write_text('{}')
        if failure == 'hash':
            candidate.write_bytes(b'changed')
        report_path = output / 'run.json'
        report_path.write_text(json.dumps(report))
        return {'candidate': str(candidate), 'candidate_sha256': digest, 'report': str(report_path),
                'production_native_export': False, 'autodesk_acceptance': 'not_tested'}

    monkeypatch.setattr(rvt_export, 'export_experimental', export)
    return calls


def job(**flags):
    return {'id': 'job', 'project_id': PID, 'input': flags}


def test_default_build_never_invokes_native_runtime(monkeypatch, tmp_path):
    calls = prepare(monkeypatch, tmp_path)
    api = FakeApi(room())
    result = build.run(api, job(), {'project': {'name': 'Test'}})
    assert calls == []
    assert set(result['keys']) == {'model.glb', 'model.ifc', 'graph.json', 'index.json'}
    assert len(api.files) == 2
    assert 'experimental_native_rvt' not in result


def test_explicit_native_success_registers_linked_evidence(monkeypatch, tmp_path):
    calls = prepare(monkeypatch, tmp_path)
    api = FakeApi(room())
    result = build.run(api, job(experimental_native_rvt=True, acknowledge_native_hypotheses=True), {'project': {'name': 'Test'}})
    assert len(calls) == 1
    assert calls[0][0]['elements'] == api.read['elements']
    assert result['experimental_native_rvt'] is True
    assert len(api.r2) == 6 and len(api.files) == 4
    native = next(f for f in api.files if f['name'].endswith('.experimental.rvt'))
    evidence_file = next(f for f in api.files if f['name'].endswith('.validation.json'))
    assert native['meta']['validation_file_id'] == evidence_file['id']
    assert native['meta']['validation_key'] == evidence_file['r2_key']
    assert evidence_file['meta']['evidence_for_key'] == native['r2_key']
    assert native['meta']['experimental'] is True and native['meta']['production_native_export'] is False
    evidence = json.loads(api.r2[evidence_file['r2_key']])
    assert evidence['candidate_sha256'] == hashlib.sha256(api.r2[native['r2_key']]).hexdigest()
    assert set(evidence['validation_reports']) == {'transport.json', 'metadata.json', 'native.json'}
    assert {b['file_id'] for b in api.messages[0]['blocks']} == {f['id'] for f in api.files}
    assert 'opening and regeneration remain unverified' in api.messages[0]['text']
    assert 'not a production-qualified' in api.revisions[0]['notes']
    assert api.revisions[0]['status'] == 'ready'
    assert not any(k.startswith('rvt') for k in api.revisions[0])


@pytest.mark.parametrize('failure', ['writer', 'audit', 'qualification', 'evidence', 'hash'])
def test_native_failure_has_no_uploads_or_ready_publication(monkeypatch, tmp_path, failure):
    prepare(monkeypatch, tmp_path, failure)
    api = FakeApi(room())
    with pytest.raises((ValueError, RuntimeError)):
        build.run(api, job(experimental_native_rvt=True, acknowledge_native_hypotheses=True), {})
    assert api.r2 == {} and api.files == [] and api.messages == [] and api.base is None
    assert api.revisions[0]['status'] == 'error'


@pytest.mark.parametrize('mode', ['no_ack', 'missing_bundle', 'missing_launcher', 'string_flag'])
def test_native_configuration_failure_never_calls_runtime_or_uploads(monkeypatch, tmp_path, mode):
    calls = prepare(monkeypatch, tmp_path)
    flags = {'experimental_native_rvt': True, 'acknowledge_native_hypotheses': True}
    if mode == 'no_ack':
        flags.pop('acknowledge_native_hypotheses')
    elif mode == 'missing_bundle':
        monkeypatch.delenv('MA_RVT_RUNTIME_BUNDLE')
    elif mode == 'missing_launcher':
        (tmp_path / 'bundle/run.py').unlink()
    else:
        flags['experimental_native_rvt'] = 'true'
    api = FakeApi(room())
    with pytest.raises(ValueError):
        build.run(api, job(**flags), {})
    assert calls == []
    assert api.r2 == {} and api.files == [] and api.base is None and api.messages == []
    assert api.revisions[0]['status'] == 'error'
