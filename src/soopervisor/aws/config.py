from soopervisor.abc import AbstractConfig
from soopervisor.enum import Backend


class AWSBatchConfig(AbstractConfig):
    repository: str

    # must not contain "image"
    container_properties: dict = {
        "memory": 16384,
        "vcpus": 8,
    }
    job_queue: str

    region_name: str

    @classmethod
    def get_backend_value(cls):
        return Backend.aws_batch.value

    @classmethod
    def defaults(cls):
        data = cls(repository='your-repository/name',
                   job_queue='your-job-queue',
                   region_name='your-region-name').dict()
        data['backend'] = cls.get_backend_value()
        del data['include']
        del data['exclude']
        return data


class AWSLambdaConfig(AbstractConfig):
    @classmethod
    def get_backend_value(cls):
        return Backend.aws_lambda.value

    @classmethod
    def defaults(cls):
        return {'backend': cls.get_backend_value()}
