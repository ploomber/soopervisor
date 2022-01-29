from soopervisor import abc
from soopervisor.enum import Backend


class AirflowConfig(abc.AbstractDockerConfig):

    @classmethod
    def get_backend_value(cls):
        return Backend.airflow.value
