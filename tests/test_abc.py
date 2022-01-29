"""
Test abstract class implementation
"""
from pathlib import Path

import click
import pytest
import yaml

from soopervisor.abc import AbstractConfig
from soopervisor.exceptions import ConfigurationFileTypeError


class ConcreteConfig(AbstractConfig):
    default: str

    @classmethod
    def get_backend_value(self):
        return 'backend-value'

    @classmethod
    def _hints(cls):
        return {'default': 'value'}


def load_config():
    return yaml.safe_load(Path('soopervisor.yaml').read_text())


def test_writes_hints_if_empty_directory(tmp_empty):
    ConcreteConfig.load_env_from_config('soopervisor.yaml', 'some_env')

    data = load_config()
    assert data['some_env']['backend'] == 'backend-value'
    assert data['some_env']['default'] == 'value'


def test_writes_hints_if_missing_env(tmp_empty):
    Path('soopervisor.yaml').write_text("""
another_env:
  key: value
""")

    ConcreteConfig.load_env_from_config('soopervisor.yaml', 'some_env')

    data = load_config()
    assert data['some_env']['backend'] == 'backend-value'
    assert data['some_env']['default'] == 'value'


@pytest.mark.parametrize('content', ['', '- a\n- b'])
def test_error_if_not_a_mapping(tmp_empty, content):
    Path('soopervisor.yaml').write_text(content)

    with pytest.raises(ConfigurationFileTypeError):
        ConcreteConfig.load_env_from_config('soopervisor.yaml', 'some_env')


def test_set_exclude_default_value(tmp_empty):
    ConcreteConfig.load_env_from_config('soopervisor.yaml',
                                        'some_env',
                                        exclude=['some-dir'])

    data = load_config()

    assert data['some_env']['exclude'] == ['some-dir']


# TODO: parametrize over concrete classes
def test_creates_soopervisor_yaml_if_it_doesnt_exist(tmp_empty):
    ConcreteConfig._write_hints_if_needed('soopervisor.yaml',
                                          'some_env',
                                          preset=None)

    cfg = load_config()
    assert cfg['some_env'] == {
        'default': 'value',
        'backend': 'backend-value',
    }


def test_error_if_root_key_exists_in_soopervisor_yaml(tmp_empty):
    Path('soopervisor.yaml').write_text('another_env:\n    x: 1')

    ConcreteConfig._write_hints_if_needed('soopervisor.yaml',
                                          'some_env',
                                          preset=None)

    cfg = load_config()

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
        CLASS_.load_env_from_config('soopervisor.yaml', 'some_env')

    assert ('Missing backend key for target some_env '
            'in soopervisor.yaml. Add it and try again.') == str(excinfo.value)


def test_error_if_invalid_backend_value(tmp_empty):
    Path('soopervisor.yaml').write_text('some_env:\n    backend: wrong-value')
