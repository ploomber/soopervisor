from pathlib import Path

import pytest
from ploomber.exceptions import DAGSpecInitializationError

from soopervisor.abc import AbstractExporter, AbstractConfig
from soopervisor.base.config import ScriptConfig


class ConcreteConfig(AbstractConfig):
    default: str = 'value'

    @classmethod
    def get_backend_value(self):
        return 'backend-value'


class ConcreteExporter(AbstractExporter):
    # TODO: the current validation depends on implementation details
    # in script config, but we should remove those
    CONFIG_CLASS = ScriptConfig

    @staticmethod
    def _add():
        pass

    @staticmethod
    def _submit():
        pass

    @staticmethod
    def _validate():
        pass


def test_error_if_missing_environment_yml(tmp_sample_project):
    Path('environment.yml').unlink()

    with pytest.raises(FileNotFoundError) as excinfo:
        ConcreteExporter('soopervisor.yaml', env_name='some_env')

    assert 'Expected a conda "environment.yml"' in str(excinfo.value)


def test_error_if_missing_name_in_environment_yml(tmp_sample_project):
    Path('environment.yml').unlink()
    Path('environment.yml').touch()

    with pytest.raises(ValueError) as excinfo:
        ConcreteExporter('soopervisor.yaml', env_name='some_env')

    assert ('Failed to extract the environment name from the '
            'conda "environment.yaml"') == str(excinfo.value)


def test_error_if_dag_fails_to_initialize(tmp_sample_project):
    Path('pipeline.yaml').unlink()

    with pytest.raises(DAGSpecInitializationError) as excinfo:
        ConcreteExporter('soopervisor.yaml', env_name='some_env')

    assert str(excinfo.value) == 'Error initializing DAG from pipeline.yaml'


# TODO: submit without adding first