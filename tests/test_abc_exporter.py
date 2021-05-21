from pathlib import Path

import pytest
from ploomber.exceptions import DAGSpecInitializationError
from click import ClickException

from soopervisor.abc import AbstractExporter, AbstractConfig


class ConcreteConfig(AbstractConfig):
    default: str = 'value'

    @classmethod
    def get_backend_value(self):
        return 'backend-value'


class ConcreteExporter(AbstractExporter):
    CONFIG_CLASS = ConcreteConfig

    @staticmethod
    def _add():
        pass

    @staticmethod
    def _export():
        pass

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass


def test_error_if_missing_environment_lock_yml(tmp_sample_project):
    Path('environment.lock.yml').unlink()

    with pytest.raises(ClickException) as excinfo:
        ConcreteExporter('soopervisor.yaml', env_name='some_env')

    assert 'Expected environment.lock.yml or requirements.txt.lock' in str(
        excinfo.value)


def test_error_if_dag_fails_to_initialize(tmp_sample_project):
    Path('pipeline.yaml').unlink()

    with pytest.raises(DAGSpecInitializationError) as excinfo:
        ConcreteExporter('soopervisor.yaml', env_name='some_env')

    assert str(excinfo.value) == 'Error initializing DAG from pipeline.yaml'


# TODO: submit without adding first
