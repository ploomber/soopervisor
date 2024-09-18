"""
Here we check the default values for each config object, this should contain
the minimum number of keys, and values should contain reasonable hints
"""

import pytest

from soopervisor.shell.config import SlurmConfig
from soopervisor.airflow.config import AirflowConfig
from soopervisor.argo.config import ArgoConfig
from soopervisor.aws.config import AWSBatchConfig, AWSLambdaConfig
from soopervisor.kubeflow.config import KubeflowConfig


@pytest.mark.parametrize(
    "class_, hints",
    [
        [
            SlurmConfig,
            {"backend": "slurm"},
        ],
        [
            AirflowConfig,
            {"backend": "airflow", "repository": "your-repository/name"},
        ],
        [
            ArgoConfig,
            {"backend": "argo-workflows", "repository": "your-repository/name"},
        ],
        [
            AWSBatchConfig,
            {
                "backend": "aws-batch",
                "container_properties": {"memory": 16384, "vcpus": 8},
                "job_queue": "your-job-queue",
                "region_name": "your-region-name",
                "repository": "your-repository/name",
            },
        ],
        [
            AWSLambdaConfig,
            {"backend": "aws-lambda"},
        ],
        [
            KubeflowConfig,
            {"backend": "kubeflow", "repository": "your-repository/name"},
        ],
    ],
)
def test_hints(class_, hints):
    """
    Test configuration hints. These are the values that the user will see
    when they create the target environment. We must ensure they contain
    meaningful values so the suer can easily understand their meaning
    (see AbstractConfiguration) for more details
    """
    assert class_.hints() == hints


@pytest.mark.parametrize(
    "class_, initial, schema",
    [
        [
            SlurmConfig,
            {},
            {"preset": None},
        ],
        [
            AirflowConfig,
            {},
            {"include": None, "exclude": None, "preset": None, "repository": None},
        ],
        [
            ArgoConfig,
            {},
            {
                "include": None,
                "exclude": None,
                "preset": None,
                "repository": None,
                "mounted_volumes": None,
            },
        ],
        [
            AWSBatchConfig,
            {
                "repository": "your-repository/name",
                "container_properties": {"memory": 16384, "vcpus": 8},
                "job_queue": "your-job-queue",
                "region_name": "your-region-name",
            },
            {
                "include": None,
                "exclude": None,
                "preset": None,
                "repository": "your-repository/name",
                "container_properties": {"memory": 16384, "vcpus": 8},
                "job_queue": "your-job-queue",
                "region_name": "your-region-name",
                "task_resources": None,
            },
        ],
        [
            AWSLambdaConfig,
            {},
            {"preset": None},
        ],
        [
            KubeflowConfig,
            {},
            {"include": None, "exclude": None, "preset": None, "repository": None},
        ],
    ],
)
def test_schema(class_, initial, schema):
    """
    Here we test the schema, we must ensure that only relevant fields appears.
    Since we create subclasses to keep the code concise, we may inadvertently
    choose the wrong superclass and add fields (or default values) that aren't
    appropriate.
    """
    assert class_(**initial).dict() == schema
