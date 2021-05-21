"""
Common tests for all implementations
"""
from pathlib import Path

import pytest

from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.airflow.export import AirflowExporter
from soopervisor.aws.batch import AWSBatchExporter


@pytest.mark.parametrize('use_pip, name', [
    [False, 'environment.lock.yml'],
    [True, 'requirements.lock.txt'],
])
@pytest.mark.parametrize('cls', [
    ArgoWorkflowsExporter,
    AirflowExporter,
    AWSBatchExporter,
])
def test_dockerfile(backup_packaged_project, use_pip, name, cls):
    if use_pip:
        Path('environment.lock.yml').unlink()
        Path('requirements.lock.txt').touch()

    exporter = cls(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.add()

    dockerfile = Path('serve', 'Dockerfile').read_text()
    expected_copy = f'COPY {name} project/{name}'
    expected_run = f'RUN mamba env update --name base --file project/{name}'
    assert expected_copy in dockerfile
    assert expected_run in dockerfile
