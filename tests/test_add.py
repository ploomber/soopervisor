"""
Common tests for all implementations
"""
from pathlib import Path

import pytest

from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.airflow.export import AirflowExporter
from soopervisor.aws.batch import AWSBatchExporter
from soopervisor.kubeflow.export import KubeflowExporter


# TODO: maybe create an abstract class for all of these so we can
# use the __subclasses__() to get them all instead of manually adding
# them
@pytest.mark.parametrize('use_pip', [False, True])
@pytest.mark.parametrize('cls', [
    ArgoWorkflowsExporter,
    AirflowExporter,
    AWSBatchExporter,
    KubeflowExporter,
])
def test_dockerfile(backup_packaged_project, use_pip, cls):
    if use_pip:
        Path('environment.lock.yml').unlink()
        Path('requirements.lock.txt').touch()
        name = 'requirements.lock.txt'
    else:
        name = 'environment.lock.yml'

    exporter = cls.new(path_to_config='soopervisor.yaml', env_name='serve')
    exporter.add()

    dockerfile = Path('serve', 'Dockerfile').read_text()
    expected_copy = f'COPY {name} project/{name}'

    if use_pip:
        expected_run = (
            'RUN pip install --requirement '
            'project/requirements.lock.txt && rm -rf /root/.cache/pip/')
    else:
        expected_run = ('RUN mamba env update --name base '
                        '--file project/environment.lock.yml')

    assert expected_copy in dockerfile
    assert expected_run in dockerfile
