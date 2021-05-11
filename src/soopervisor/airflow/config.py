from soopervisor import abc
from soopervisor.enum import Backend


class AirflowConfig(abc.AbstractConfig):
    @classmethod
    def get_backend_value(cls):
        return Backend.airflow.value

    @classmethod
    def defaults(cls):
        data = cls().dict()
        data['backend'] = cls.get_backend_value()
        return data
