from soopervisor import abc
from soopervisor.enum import Backend


class KubeflowConfig(abc.AbstractDockerConfig):

    @classmethod
    def get_backend_value(cls):
        return Backend.kubeflow.value
