"""
Test abstract class implementation
"""
from pathlib import Path

import click
import pytest
import yaml

from soopervisor.abc import AbstractConfig
# from soopervisor.airflow.config import AirflowConfig


class ConcreteConfig(AbstractConfig):
    default: str

    @classmethod
    def get_backend_value(self):
        return 'backend-value'

    @classmethod
    def _hints(cls):
        return {'default': 'value'}


def test_initialize_from_empty_folder(tmp_empty):
    ConcreteConfig.from_file_with_root_key('soopervisor.yaml', 'some_env')

    data = yaml.safe_load(Path('soopervisor.yaml').read_text())
    assert data['some_env']['backend'] == 'backend-value'
    assert data['some_env']['default'] == 'value'


def test_set_exclude_default_value(tmp_empty):
    ConcreteConfig.from_file_with_root_key('soopervisor.yaml',
                                           'some_env',
                                           exclude=['some-dir'])

    data = yaml.safe_load(Path('soopervisor.yaml').read_text())

    assert data['some_env']['exclude'] == ['some-dir']


# TODO: parametrize over concrete classes
def test_creates_soopervisor_yaml_if_it_doesnt_exist(tmp_empty):
    ConcreteConfig._write_defaults('soopervisor.yaml', 'some_env', preset=None)

    cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())
    assert cfg['some_env'] == {
        'default': 'value',
        'backend': 'backend-value',
    }


def test_error_if_root_key_exists_in_soopervisor_yaml(tmp_empty):
    Path('soopervisor.yaml').write_text('another_env:\n    x: 1')

    ConcreteConfig._write_defaults('soopervisor.yaml', 'some_env', preset=None)

    cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())

    assert cfg['another_env']['x'] == 1
    assert cfg['some_env']['default'] == 'value'


@pytest.mark.parametrize(
    'CLASS_, data',
    [
        [ConcreteConfig, {}],
        # [AirflowConfig, {}],
    ])
def test_error_if_missing_backend_key_in_soopervisor(CLASS_, data, tmp_empty):
    Path('soopervisor.yaml').write_text(yaml.safe_dump({'some_env': data}))

    with pytest.raises(click.ClickException) as excinfo:
        CLASS_.from_file_with_root_key('soopervisor.yaml', 'some_env')

    assert ('Missing backend key for target some_env '
            'in soopervisor.yaml. Add it and try again.') == str(excinfo.value)


def test_error_if_invalid_backend_value(tmp_empty):
    Path('soopervisor.yaml').write_text('some_env:\n    backend: wrong-value')
    # ConcreteConfig.from_file_with_root_key('soopervisor.yaml', 'some_env')


def test_error_if_target_directory_exists_and_not_empty(tmp_empty):
    pass


def test_error_if_missing_dot_git():
    """Projects must be in a git repository
    """
    pass
