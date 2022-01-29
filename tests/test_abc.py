"""
Test abstract class implementation
"""
from pathlib import Path

import pytest
import yaml

from soopervisor.abc import AbstractConfig, AbstractDockerConfig
from soopervisor.exceptions import (ConfigurationFileTypeError,
                                    ConfigurationError)


class ConcreteConfig(AbstractConfig):
    default: str

    @classmethod
    def get_backend_value(self):
        return 'backend-value'

    @classmethod
    def _hints(cls):
        return {'default': 'value'}


class ConcreteDockerConfig(AbstractDockerConfig):

    @classmethod
    def get_backend_value(self):
        return 'backend-value'

    @classmethod
    def _hints(cls):
        return {}


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


def test_error_if_section_is_not_a_mapping(tmp_empty):
    Path('soopervisor.yaml').write_text("""
some_env: [1, 2, 3]
""")

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteConfig.load_env_from_config('soopervisor.yaml', 'some_env')

    expected = ("Expected key 'some_env' in 'soopervisor.yaml' to contain "
                "a dictionary, got list")

    assert str(excinfo.value) == expected


def test_docker_config_pass_exclude_value(tmp_empty):
    ConcreteDockerConfig.load_env_from_config('soopervisor.yaml',
                                              'some_env',
                                              exclude=['some-dir'])

    data = load_config()

    assert data['some_env']['exclude'] == ['some-dir']


def test_write_hints_if_needed_doesnt_rewrite_content(tmp_empty):
    Path('soopervisor.yaml').write_text("""
another_env:
    x: 1
""")

    ConcreteConfig._write_hints_if_needed('soopervisor.yaml',
                                          'some_env',
                                          preset=None)

    cfg = load_config()

    assert cfg['another_env']['x'] == 1
    assert cfg['some_env']['default'] == 'value'


@pytest.mark.parametrize('CLASS_', [
    ConcreteConfig,
    ConcreteDockerConfig,
])
def test_error_if_missing_backend_key_in_soopervisor(CLASS_, tmp_empty):
    Path('soopervisor.yaml').write_text(yaml.safe_dump({'some_env': {}}))

    with pytest.raises(ConfigurationError) as excinfo:
        CLASS_.load_env_from_config('soopervisor.yaml', 'some_env')

    assert ("Missing 'backend' key for section 'some_env' "
            "in 'soopervisor.yaml'. Add it and try again.") == str(
                excinfo.value)


def test_error_if_invalid_backend_value(tmp_empty):
    Path('soopervisor.yaml').write_text('some_env:\n    backend: wrong-value')

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteDockerConfig.load_env_from_config('soopervisor.yaml',
                                                  'some_env')

    expected = ("Invalid backend key for section 'some_env' in "
                "soopervisor.yaml. Expected 'backend-value', "
                "actual 'wrong-value'")
    assert str(excinfo.value) == expected
