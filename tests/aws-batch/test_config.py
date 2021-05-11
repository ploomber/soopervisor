from soopervisor.aws.config import AWSBatchConfig


def test_defaults(tmp_empty):
    cfg = AWSBatchConfig.from_file_with_root_key('soopervisor.yaml', 'env')
    assert cfg.dict() == {
        'repository': 'your-repository/name',
        'container_properties': {
            'memory': 16384,
            'vcpus': 8
        },
        'job_queue': 'your-job-queue',
        'region_name': 'your-region-name'
    }
