from soopervisor import abc
from soopervisor.enum import Backend


# FIXME: this requires further validation because
# depending on the preset, some fields aren't relevant,
# e.g., if using bash, include, exclude and repository
# are not allowed
class AirflowConfig(abc.AbstractDockerConfig):

    @classmethod
    def get_backend_value(cls):
        return Backend.airflow.value

    @classmethod
    def get_presets(cls):
        return ('kubernetes', 'bash', 'docker')
