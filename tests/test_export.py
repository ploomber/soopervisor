import shutil
import sys
from unittest.mock import Mock
import os
from pathlib import Path

import pytest
import boto3
import docker

from conftest import git_init
from soopervisor.airflow.export import (AirflowExporter, commons as
                                        airflow_commons)
from soopervisor.argo.export import (ArgoWorkflowsExporter, commons as
                                     argo_commons)
from soopervisor.aws.batch import (AWSBatchExporter, commons as batch_commons)
from soopervisor.kubeflow.export import (KubeflowExporter, commons as
                                         kubeflow_commons)
from soopervisor.shell.export import SlurmExporter
from soopervisor.aws import batch
from soopervisor.exceptions import ConfigurationError

CLASSES = [
    AirflowExporter,
    ArgoWorkflowsExporter,
    AWSBatchExporter,
    KubeflowExporter,
]


@pytest.mark.parametrize('CLASS_', CLASSES)
def test_dockerfile_when_no_setup_py(CLASS_, tmp_sample_project,
                                     no_sys_modules_cache):
    exporter = CLASS_.new(path_to_config='soopervisor.yaml', env_name='serve')

    exporter.add()

    dockerfile = Path('serve', 'Dockerfile').read_text()
    assert 'RUN pip install *.tar.gz --no-deps' not in dockerfile


@pytest.mark.parametrize('CLASS_, files', [
    [
        AirflowExporter,
        {'sample_project.py', 'Dockerfile'},
    ],
    [
        ArgoWorkflowsExporter,
        {'Dockerfile'},
    ],
    [
        AWSBatchExporter,
        {'Dockerfile'},
    ],
    [
        KubeflowExporter,
        {'Dockerfile'},
    ],
    [
        SlurmExporter,
        {'template.sh'},
    ],
])
def test_add_creates_necessary_files(CLASS_, files, tmp_sample_project,
                                     no_sys_modules_cache):
    exporter = CLASS_.new(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.add()

    assert set(os.listdir('serve')) == files


@pytest.fixture
def monkeypatch_boto3_batch_client(monkeypatch):
    """
    Mocks calls to boto3.client(...) in the batch module
    """
    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)


@pytest.fixture
def mock_docker_and_batch(
    mock_batch,
    mock_docker_sample_project,
    monkeypatch_docker_client,
    monkeypatch_boto3_batch_client,
):
    pass


# TODO: add the missing ones and copy the duplicates (lambda)
@pytest.mark.parametrize('CLASS_', [
    AWSBatchExporter,
    AirflowExporter,
    ArgoWorkflowsExporter,
    KubeflowExporter,
],
                         ids=[
                             'batch',
                             'airflow',
                             'argo',
                             'kubeflow',
                         ])
def test_skip_tests(
    mock_docker_and_batch,
    tmp_sample_project,
    no_sys_modules_cache,
    skip_repo_validation,
    capsys,
    CLASS_,
):

    exporter = CLASS_.new(path_to_config='soopervisor.yaml', env_name='serve')

    exporter.add()
    exporter.export(mode='incremental', skip_tests=True)

    captured = capsys.readouterr()
    assert 'Testing image' not in captured.out
    assert 'Testing File client' not in captured.out


# TODO: check missing
@pytest.mark.parametrize('CLASS, commons', [
    [AirflowExporter, airflow_commons],
    [KubeflowExporter, kubeflow_commons],
    [AWSBatchExporter, batch_commons],
    [ArgoWorkflowsExporter, argo_commons],
])
def test_stops_if_no_tasks(monkeypatch, mock_docker_sample_project,
                           tmp_sample_project, no_sys_modules_cache, capsys,
                           CLASS, commons):
    load_tasks_mock = Mock(return_value=([], []))
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = CLASS.new(path_to_config='soopervisor.yaml', env_name='serve')

    git_init()

    exporter.add()
    exporter.export(mode='incremental')

    captured = capsys.readouterr()
    assert 'has no tasks to submit.' in captured.out


# TODO: add missing, enable aws batch
@pytest.mark.parametrize(
    'CLASS',
    [
        ArgoWorkflowsExporter,
        KubeflowExporter,
        # AWSBatchExporter,
        AirflowExporter,
    ])
def test_checks_the_right_spec(monkeypatch, mock_docker_sample_project_serve,
                               tmp_sample_project, no_sys_modules_cache,
                               skip_repo_validation, CLASS):
    shutil.copy('pipeline.yaml', 'pipeline.serve.yaml')

    exporter = CLASS.new(path_to_config='soopervisor.yaml', env_name='serve')

    exporter.add()
    exporter.export(mode='incremental')

    expected = ('docker', 'run', 'sample_project:latest-default', 'ploomber',
                'status', '--entry-point', 'pipeline.serve.yaml')
    assert mock_docker_sample_project_serve.calls[1] == expected


# TODO: add missing, enable aws batch
@pytest.mark.parametrize(
    'CLASS',
    [
        ArgoWorkflowsExporter,
        KubeflowExporter,
        # AWSBatchExporter,
        AirflowExporter,
    ])
def test_checks_the_right_spec_pkg(mock_docker_my_project_serve,
                                   backup_packaged_project, monkeypatch,
                                   skip_repo_validation, CLASS):
    shutil.copy('src/my_project/pipeline.yaml',
                'src/my_project/pipeline.serve.yaml')

    exporter = CLASS.new(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.add()
    exporter.export(mode='incremental')

    expected = ('docker', 'run', 'my_project:0.1dev-default', 'ploomber',
                'status', '--entry-point',
                str(Path('src', 'my_project', 'pipeline.serve.yaml')))
    assert mock_docker_my_project_serve.calls[2] == expected


# TODO: add missing
@pytest.mark.parametrize('CLASS', [
    ArgoWorkflowsExporter,
    KubeflowExporter,
    AWSBatchExporter,
    AirflowExporter,
])
def test_validates_repository(mock_docker_sample_project, tmp_sample_project,
                              CLASS):
    exporter = CLASS.new(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.add()

    with pytest.raises(ConfigurationError) as excinfo:
        exporter.export(mode='incremental', until=None, skip_tests=True)

    assert str(
        excinfo.value) == ("Invalid repository 'your-repository/name' "
                           "in soopervisor.yaml, please add a valid value.")


@pytest.mark.xfail(sys.platform == "darwin", reason="Docker not supported")
@pytest.mark.xfail(sys.platform == "win32", reason="Docker not supported")
@pytest.mark.parametrize('CLASS_', [
    ArgoWorkflowsExporter,
],
                         ids=[
                             'argo-workflows',
                         ])
def test_docker_local_lib_import(
    tmp_sample_project,
    no_sys_modules_cache,
    skip_repo_validation,
    CLASS_,
):

    text = "serve: {backend: argo-workflows, repository: null}"

    exporter = CLASS_.new(path_to_config='soopervisor.yaml', env_name='serve')

    Path('soopervisor.yaml').write_text(text)

    exporter.add()

    # reload exporter so it picks up the edited soopervisor.yaml
    exporter = CLASS_.load(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.export(mode='incremental', skip_tests=True)

    client = docker.from_env()

    # sleep 1 seems to fix this test on my machine
    # may be related to this?:
    # https://github.com/docker/docker-py/issues/2087
    import_suc = client.containers.run(
        "sample_project:latest-default", "/bin/bash -c \"sleep 1 "
        "&& python -c 'from lib import package_a; "
        "package_a.print_hello()'\"")

    assert import_suc == b'hello\n'

    try:
        client.containers.run("sample_project:latest-default",
                              "python -c 'from lib import package_b;'")
    except docker.errors.ContainerError as e:
        assert e.exit_status == 1


@pytest.mark.parametrize('CLASS_', CLASSES)
def test_skip_docker(
    mock_docker_and_batch,
    tmp_sample_project,
    no_sys_modules_cache,
    skip_repo_validation,
    capsys,
    CLASS_,
):
    modes = ['incremental', 'regular', 'force']
    asserts = []
    for mode in modes:
        exporter = CLASS_.new(path_to_config='soopervisor.yaml',
                              env_name=f'serve_{mode}')
        exporter.add()
        exporter.export(mode=mode, skip_docker=True)
        out, err = capsys.readouterr()
        assert_ = ('Skipping docker build' in out
                   and 'Building image' not in out)
        asserts.append(assert_)

    assert all(asserts)


@pytest.mark.parametrize('CLASS_', CLASSES)
def test_skip_docker_false(
    mock_docker_and_batch,
    tmp_sample_project,
    no_sys_modules_cache,
    skip_repo_validation,
    capsys,
    CLASS_,
):
    modes = ['incremental', 'regular', 'force']
    asserts = []
    for mode in modes:
        exporter = CLASS_.new(path_to_config='soopervisor.yaml',
                              env_name=f'serve_{mode}')
        exporter.add()
        exporter.export(mode=mode, skip_docker=False)
        out, err = capsys.readouterr()
        assert_ = ('Skipping docker build' not in out
                   and 'Building image' in out)
        asserts.append(assert_)

    assert all(asserts)
