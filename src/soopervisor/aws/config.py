from soopervisor.abc import AbstractConfig, AbstractDockerConfig
from soopervisor.enum import Backend


class AWSBatchConfig(AbstractDockerConfig):
    # in AWSBatch, repository cannot be None
    repository: str

    container_properties: dict
    job_queue: str
    region_name: str

    @classmethod
    def get_backend_value(cls):
        return Backend.aws_batch.value

    @classmethod
    def _hints(cls):
        return dict(repository='your-repository/name',
                    job_queue='your-job-queue',
                    region_name='your-region-name',
                    container_properties=dict(
                        memory=16384,
                        vcpus=8,
                    ))


class AWSLambdaConfig(AbstractConfig):

    @classmethod
    def get_backend_value(cls):
        return Backend.aws_lambda.value
