"""Offline runtime boundary fails closed on omissions or invalid publication."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from ma_proc.model.rvt_export import export_experimental


def test_requires_ack_and_new_destination(tmp_path):
    with pytest.raises(ValueError, match='acknowledged'):
        export_experimental({}, tmp_path, tmp_path / 'out')
    with pytest.raises(FileExistsError):
        export_experimental({}, tmp_path, tmp_path, acknowledge_hypotheses=True)


@pytest.mark.parametrize('failure', [None, 'status', 'hash', 'qualification'])
def test_runtime_publication_contract(tmp_path, failure):
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    (bundle / 'run.py').write_text('# launcher fixture')
    output = tmp_path / 'out'
    request = {'units': 'metres', 'elements': [{'id': 'app-id'}]}

    def run(command, check):
        assert check and command[-1] == '--acknowledge-hypotheses'
        saved = Path(command[command.index('--request') + 1])
        assert json.loads(saved.read_bytes()) == request
        output.mkdir()
        (output / 'verified-candidate.rvt').write_bytes(b'candidate fixture')
        report = {'status': 'verified_research_candidate',
                  'candidate_sha256': hashlib.sha256(b'candidate fixture').hexdigest(),
                  'production_native_export': False}
        if failure == 'status': report['status'] = 'failed'
        if failure == 'hash': report['candidate_sha256'] = '0' * 64
        if failure == 'qualification': report['production_native_export'] = True
        (output / 'run.json').write_text(json.dumps(report))

    with patch('ma_proc.model.rvt_export.Model'), patch('ma_proc.model.rvt_export.all_parts'), \
         patch('ma_proc.model.rvt_export.to_seed_model_request', return_value=request), \
         patch('ma_proc.model.rvt_export.subprocess.run', side_effect=run):
        if failure:
            with pytest.raises(ValueError):
                export_experimental({}, bundle, output, acknowledge_hypotheses=True)
        else:
            result = export_experimental({}, bundle, output, acknowledge_hypotheses=True)
            assert result['production_native_export'] is False
            assert result['autodesk_acceptance'] == 'not_tested'


def test_omitted_geometry_never_launches_runtime(tmp_path):
    (tmp_path / 'run.py').write_text('# launcher fixture')
    with patch('ma_proc.model.rvt_export.Model'), patch('ma_proc.model.rvt_export.all_parts'), \
         patch('ma_proc.model.rvt_export.to_seed_model_request', side_effect=ValueError('missing geometry')), \
         patch('ma_proc.model.rvt_export.subprocess.run') as run:
        with pytest.raises(ValueError, match='missing geometry'):
            export_experimental({}, tmp_path, tmp_path / 'out', acknowledge_hypotheses=True)
        run.assert_not_called()
