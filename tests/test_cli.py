import pytest
from click.testing import CliRunner

from soopervisor.cli import cli


@pytest.mark.parametrize('args', [
    ['add', 'serve', '--backend', 'argo-workflows'],
    ['add', 'serve', '--backend', 'airflow'],
])
def test_export_sample_project(args, tmp_sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0


@pytest.mark.parametrize('args', [
    ['add', 'serve', '--backend', 'argo-workflows'],
    ['add', 'serve', '--backend', 'airflow'],
])
def test_export_callables(args, tmp_callables):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
