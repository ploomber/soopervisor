"""
Here we check the default values for each config object, this should contain
the minimum number of keys, and values should contain reasonable defaults
"""
import pytest

from soopervisor.shell.config import SlurmConfig
from soopervisor.airflow.config import AirflowConfig
from soopervisor.argo.config import ArgoConfig
from soopervisor.aws.config import AWSBatchConfig, AWSLambdaConfig
from soopervisor.kubeflow.config import KubeflowConfig


@pytest.mark.parametrize('class_, defaults', [
    [
        SlurmConfig,
        {
            'backend': 'slurm'
        },
    ],
    [
        AirflowConfig,
        {
            'backend': 'airflow',
            'repository': 'your-repository/name'
        },
    ],
    [
        ArgoConfig,
        {
            'backend': 'argo-workflows',
            'repository': 'your-repository/name'
        },
    ],
    [
        AWSBatchConfig,
        {
            'backend': 'aws-batch',
            'container_properties': {
                'memory': 16384,
                'vcpus': 8
            },
            'job_queue': 'your-job-queue',
            'region_name': 'your-region-name',
            'repository': 'your-repository/name'
        },
    ],
    [
        AWSLambdaConfig,
        {
            'backend': 'aws-lambda'
        },
    ],
    [
        KubeflowConfig,
        {
            'backend': 'kubeflow',
            'repository': 'your-repository/name'
        },
    ],
])
def test_defaults(class_, defaults):
    assert class_.defaults() == defaults
