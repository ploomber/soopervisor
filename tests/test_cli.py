from unittest.mock import Mock, call

import yaml
import pytest
from click.testing import CliRunner

from soopervisor.cli import cli
from soopervisor.script.cli import _make_script
from soopervisor.executors.LocalExecutor import LocalExecutor
from soopervisor.argo import export as argo_export


def null_execute(self):
    pass


@pytest.mark.parametrize('args', [
    ['build'],
    ['build', '--clean-products-path'],
])
def test_build(args, monkeypatch, tmp_sample_project, git_hash):
    monkeypatch.setattr(LocalExecutor, 'execute', null_execute)
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0


@pytest.mark.parametrize('args', [
    ['export'],
    ['export-airflow'],
])
def test_export_sample_project(args, tmp_sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0


@pytest.mark.parametrize('args', [
    ['export'],
    ['export-airflow'],
])
def test_export_callables(args, tmp_callables):
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0


def test_export_with_upload(monkeypatch, tmp_sample_project):
    m_stdout = Mock()
    m_stdout.stdout = b'some_pod_id'
    m = Mock(return_value=m_stdout)

    config = {
        'code_pod': {
            "args": "-l role=nfs-server",
            "path": "/exports/{{project_name}}"
        }
    }

    with open('soopervisor.yaml', 'w') as f:
        yaml.dump(config, f)

    monkeypatch.setattr(argo_export.subprocess, 'run', m)

    runner = CliRunner()
    result = runner.invoke(cli, ['export', '--upload'])

    call_one, call_two = m.call_args_list

    assert call_one == call([
        'kubectl',
        'get',
        'pods',
        '--output',
        'jsonpath="{.items[0].metadata.name}"',
        '-l',
        'role=nfs-server',
    ],
                            check=True,
                            capture_output=True)

    assert call_two == call([
        'kubectl',
        'cp',
        str(tmp_sample_project),
        'some_pod_id:/exports/sample_project',
    ])

    assert m.call_count == 2
    assert result.exit_code == 0


def test_export_with_upload_missing_code_pod(tmp_sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['export', '--upload'])

    assert isinstance(result.exception, ValueError)
    assert '"code_pod" section in the configuration file' in str(
        result.exception)
    assert result.exit_code == 1


def test_make_script(tmp_sample_project):
    runner = CliRunner()
    result = runner.invoke(_make_script, ['ploomber build'])
    assert result.exit_code == 0
