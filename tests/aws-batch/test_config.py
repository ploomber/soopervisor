from soopervisor.aws.config import AWSBatchConfig


def test_defaults():
    cfg = AWSBatchConfig.defaults()
    assert cfg == {
        'backend': 'aws-batch',
        'repository': 'your-repository/name',
        'container_properties': {
            'memory': 16384,
            'vcpus': 8
        },
        'job_queue': 'your-job-queue',
        'region_name': 'your-region-name'
    }
