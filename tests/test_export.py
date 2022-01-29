from pathlib import Path

import pytest

from soopervisor.airflow.export import AirflowExporter
from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.aws.batch import AWSBatchExporter
from soopervisor.kubeflow.export import KubeflowExporter


@pytest.mark.parametrize('CLASS_', [
    AirflowExporter,
    ArgoWorkflowsExporter,
    AWSBatchExporter,
    KubeflowExporter,
])
def test_dockerfile_when_no_setup_py(CLASS_, tmp_sample_project,
                                     no_sys_modules_cache):
    exporter = CLASS_.new(path_to_config='soopervisor.yaml', env_name='serve')

    exporter.add()

    dockerfile = Path('serve', 'Dockerfile').read_text()
    assert 'RUN pip install *.tar.gz --no-deps' not in dockerfile
