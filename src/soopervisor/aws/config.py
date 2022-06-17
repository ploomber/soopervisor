from typing import Mapping

from pydantic import BaseModel

from soopervisor.abc import AbstractConfig, AbstractDockerConfig
from soopervisor.enum import Backend


class TaskResource(BaseModel):
    vcpus: int = None
    memory: int = None
    gpu: int = None

    class Config:
        extra = 'forbid'


class AWSBatchConfig(AbstractDockerConfig):
    # in AWSBatch, repository cannot be None
    repository: str

    container_properties: dict
    job_queue: str
    region_name: str

    task_resources: Mapping[str, TaskResource] = None

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


class CloudConfig(AWSBatchConfig):
    @classmethod
    def get_backend_value(cls):
        return Backend.cloud.value


class AWSLambdaConfig(AbstractConfig):
    @classmethod
    def get_backend_value(cls):
        return Backend.aws_lambda.value
