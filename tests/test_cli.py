from pathlib import Path
from unittest.mock import Mock, ANY

import tarfile
import yaml
import pytest
from click.testing import CliRunner

from soopervisor.cli import cli
from soopervisor.cli import exporter
from soopervisor.enum import Backend
from soopervisor.argo import export as argo_export
from soopervisor.airflow import export as airflow_export
from soopervisor.aws import batch
from soopervisor.commons import docker

from conftest import CustomCommander


@pytest.fixture
def monkeypatch_external(monkeypatch):
    monkeypatch.setattr(argo_export, 'Commander', CustomCommander)
    monkeypatch.setattr(airflow_export, 'Commander', CustomCommander)
    monkeypatch.setattr(batch, 'Commander', CustomCommander)
    monkeypatch.setattr(batch, '_submit_dag', Mock())
    mock_copy = Mock(wraps=docker.source.copy)
    monkeypatch.setattr(docker.source, 'copy', mock_copy)
    return mock_copy


# TODO Add test with lambda


def test_add_unknown_backend():
    runner = CliRunner()
    result = runner.invoke(cli, ['add', 'something', '--backend', 'unknown'],
                           catch_exceptions=False)
    assert result.exit_code == 2
    assert "Invalid value for '--backend' / '-b'" in result.stdout


def test_export_missing_soopervisor_yaml(tmp_empty):
    runner = CliRunner()
    result = runner.invoke(cli, ['export', 'something'],
                           catch_exceptions=False)

    expected = ("Error: Expected a 'soopervisor.yaml' file in the "
                "current working directory, but such files does not exist\n")
    assert result.exit_code == 1
    assert result.output == expected


@pytest.mark.skip(reason='current implementation overwrites .tar.gz contents')
@pytest.mark.parametrize(
    'args, backend',
    [[['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
     [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
     [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch]],
    ids=['argo', 'airflow', 'aws-batch'])
def test_p_home_exists_tar(args, backend, tmp_sample_project, monkeypatch,
                           monkeypatch_external):
    monkeypatch.delenv('PLOOMBER_STATS_ENABLED', raising=True)
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0

    with open('soopervisor.yaml', 'r') as file:
        yml = yaml.safe_load(file)
    yml['serve']['repository'] = 'null'

    with open('soopervisor.yaml', 'w') as file:
        yaml.dump(yml, file)
    file.close()
    result = runner.invoke(cli, ['export', '-i', '-s', 'serve'],
                           catch_exceptions=False)

    # Check workspace files exist after execution
    # Extracting targz file
    tar_path = Path('dist', 'sample_project.tar.gz')
    file = tarfile.open(tar_path)
    file.extractall('.')
    file.close()

    # Load stats
    stats_path = Path('ploomber', 'stats')
    conf = Path(stats_path, 'config.yaml')
    uid = Path(stats_path, 'uid.yaml')

    assert conf.exists()
    assert uid.exists()


@pytest.mark.parametrize('backend', [
    'argo-workflows',
    'aws-batch',
    'slurm',
    'aws-lambda',
])
def test_error_if_backend_takes_no_preset(tmp_sample_project, backend):
    runner = CliRunner()

    res = runner.invoke(cli, [
        'add',
        'something',
        '--backend',
        backend,
        '--preset',
        'some-preset',
    ])

    assert res.exit_code
    assert 'does not have presets' in res.stdout


@pytest.mark.parametrize('backend, preset', [
    ['airflow', 'invalid'],
])
def test_error_if_invalid_preset(tmp_sample_project, backend, preset):
    runner = CliRunner()

    res = runner.invoke(cli, [
        'add',
        'something',
        '--backend',
        backend,
        '--preset',
        preset,
    ])

    assert res.exit_code
    expected = ("Error: Preset 'invalid' is not a valid value for "
                "backend 'airflow'. Valid presets are: 'kubernetes', 'bash'")
    assert expected in res.stdout


@pytest.mark.parametrize('backend, preset', [
    ['airflow', 'bash'],
    ['airflow', 'kubernetes'],
])
def test_accepts_preset_value(tmp_sample_project, backend, preset):
    runner = CliRunner()

    res = runner.invoke(cli, [
        'add',
        'something',
        '--backend',
        backend,
        '--preset',
        preset,
    ])

    assert res.exit_code == 0


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'kubeflow'], Backend.kubeflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'kubeflow',
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
    exporter_.load.assert_called_once_with('soopervisor.yaml',
                                           env_name='serve')
    exporter_.load().export.assert_called_once_with(mode='incremental',
                                                    until=None,
                                                    skip_tests=False,
                                                    ignore_git=False)


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'kubeflow'], Backend.kubeflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'kubeflow',
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
    exporter_.load.assert_called_once_with('soopervisor.yaml',
                                           env_name='serve')
    exporter_.load().export.assert_called_once_with(mode=mode,
                                                    until=None,
                                                    skip_tests=False,
                                                    ignore_git=False)


@pytest.mark.parametrize('args', [
    ['add', 'serve', '--backend', 'argo-workflows'],
    ['add', 'serve', '--backend', 'airflow'],
    ['add', 'serve', '--backend', 'kubeflow'],
    ['add', 'serve', '--backend', 'aws-batch'],
    ['add', 'serve', '--backend', 'slurm'],
],
                         ids=[
                             'argo',
                             'airflow',
                             'kubeflow',
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
    [['add', 'serve', '--backend', 'kubeflow'], Backend.kubeflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
    [['add', 'serve', '--backend', 'slurm'], Backend.slurm],
],
                         ids=[
                             'argo',
                             'airflow',
                             'kubeflow',
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
    exporter_.load.assert_called_once_with('soopervisor.yaml',
                                           env_name='serve')
    exporter_.load().export.assert_called_once_with(mode='incremental',
                                                    until=None,
                                                    skip_tests=True,
                                                    ignore_git=False)


@pytest.mark.parametrize('args, backend', [
    [['add', 'serve', '--backend', 'argo-workflows'], Backend.argo_workflows],
    [['add', 'serve', '--backend', 'airflow'], Backend.airflow],
    [['add', 'serve', '--backend', 'aws-batch'], Backend.aws_batch],
],
                         ids=[
                             'argo',
                             'airflow',
                             'batch',
                         ])
def test_ignore_git(args, backend, tmp_sample_project, monkeypatch_external):
    runner = CliRunner()
    # add target environment with all backends
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0

    f = Path('soopervisor.yaml')

    if backend != Backend.aws_batch:
        new = f.read_text().replace('your-repository/name', 'null')
    else:
        new = f.read_text().replace('your-repository/name',
                                    'your-repository/something')

    f.write_text(new)

    # test export with --ignore-git
    result = runner.invoke(cli, ['export', 'serve', '--ignore-git'],
                           catch_exceptions=False)
    assert result.exit_code == 0

    monkeypatch_external.assert_called_once_with(cmdr=ANY,
                                                 src='.',
                                                 dst=Path(
                                                     'dist', 'sample_project'),
                                                 include=None,
                                                 exclude=None,
                                                 ignore_git=True)
