from typing import Optional

from soopervisor import abc
from soopervisor.enum import Backend


class AirflowConfig(abc.AbstractConfig):
    repository: Optional[str] = None

    @classmethod
    def get_backend_value(cls):
        return Backend.airflow.value

    @classmethod
    def defaults(cls):
        data = cls(repository='your-repository/name').dict()
        data['backend'] = cls.get_backend_value()
        del data['include']
        del data['exclude']
        return data
