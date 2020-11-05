import pytest
from click.testing import CliRunner

from soopervisor.cli import cli
from soopervisor.script.cli import _make_script
from soopervisor.executors.LocalExecutor import LocalExecutor


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


def test_make_script(tmp_sample_project):
    runner = CliRunner()
    result = runner.invoke(_make_script, ['ploomber build'])
    assert result.exit_code == 0
