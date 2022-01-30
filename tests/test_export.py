from unittest.mock import Mock
import os
from pathlib import Path

import pytest
import boto3

from conftest import _mock_docker_calls, git_init
from soopervisor.airflow.export import (AirflowExporter, commons as
                                        airflow_commons)
from soopervisor.argo.export import (ArgoWorkflowsExporter, commons as
                                     argo_commons)
from soopervisor.aws.batch import (AWSBatchExporter, commons as batch_commons)
from soopervisor.kubeflow.export import (KubeflowExporter, commons as
                                         kubeflow_commons)
from soopervisor.shell.export import SlurmExporter
from soopervisor.aws import batch

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


# TODO: this is still duplicated in a few places
@pytest.fixture
def mock_docker_calls(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_docker_calls(monkeypatch, cmd, 'sample_project', 'latest')


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
    mock_docker_calls,
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
def test_stops_if_no_tasks(monkeypatch, mock_docker_calls, tmp_sample_project,
                           no_sys_modules_cache, capsys, CLASS, commons):
    load_tasks_mock = Mock(return_value=([], []))
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = CLASS.new(path_to_config='soopervisor.yaml', env_name='serve')

    git_init()

    exporter.add()
    exporter.export(mode='incremental')

    captured = capsys.readouterr()
    assert 'has no tasks to submit.' in captured.out
