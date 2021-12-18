from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from soopervisor.cli import cli
from soopervisor.cli import exporter
from soopervisor.enum import Backend

# TODO Add test with lambda


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'batch',
                             'slurm',
                         ])
def test_sample_project_no_args(args, backend, tmp_sample_project,
                                monkeypatch):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0

    exporter_ = Mock()
    for_backend = Mock(return_value=exporter_)
    monkeypatch.setattr(exporter, 'for_backend', for_backend)

    result = runner.invoke(cli, ['export', 'serve'], catch_exceptions=False)
    assert result.exit_code == 0

    # check calls to the python API
    for_backend.assert_called_once_with(backend)
    exporter_.assert_called_once_with('soopervisor.yaml', env_name='serve')
    exporter_().export.assert_called_once_with(mode='incremental',
                                               until=None,
                                               skip_tests=False)


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'batch',
                             'slurm',
                         ])
@pytest.mark.parametrize('args_export, mode', [
    [['--mode', 'incremental'], 'incremental'],
    [['--mode', 'regular'], 'regular'],
    [['--mode', 'force'], 'force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_sample_project(args, args_export, mode, backend, tmp_sample_project,
                        monkeypatch):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0

    exporter_ = Mock()
    for_backend = Mock(return_value=exporter_)
    monkeypatch.setattr(exporter, 'for_backend', for_backend)

    result = runner.invoke(cli, ['export', 'serve'] + args_export,
                           catch_exceptions=False)
    assert result.exit_code == 0

    # check calls to the python API
    for_backend.assert_called_once_with(backend)
    exporter_.assert_called_once_with('soopervisor.yaml', env_name='serve')
    exporter_().export.assert_called_once_with(mode=mode,
                                               until=None,
                                               skip_tests=False)


@pytest.mark.parametrize('args', [
    ['add', 'serve', '--backend', 'argo-workflows'],
    ['add', 'serve', '--backend', 'airflow'],
    ['add', 'serve', '--backend', 'aws-batch'],
    ['add', 'serve', '--backend', 'slurm'],
],
                         ids=[
                             'argo',
                             'airflow',
                             'batch',
                             'slurm',
                         ])
def test_callables(args, tmp_callables):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'batch',
                             'slurm',
                         ])
def test_skip_tests(args, backend, tmp_sample_project, monkeypatch):
    runner = CliRunner()
    # add target environment with all backends
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0

    exporter_ = Mock()
    for_backend = Mock(return_value=exporter_)
    monkeypatch.setattr(exporter, 'for_backend', for_backend)

    # test export with --skip-tests
    result = runner.invoke(cli, ['export', 'serve', '--skip-tests'],
                           catch_exceptions=False)
    assert result.exit_code == 0

    # check calls to the python API
    for_backend.assert_called_once_with(backend)
    exporter_.assert_called_once_with('soopervisor.yaml', env_name='serve')
    exporter_().export.assert_called_once_with(mode='incremental',
                                               until=None,
                                               skip_tests=True)
