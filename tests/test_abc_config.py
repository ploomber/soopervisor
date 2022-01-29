"""
Test abstract class implementation
"""
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

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


@pytest.mark.parametrize('method, kind', [
    ['mkdir', 'directory'],
    ['touch', 'file'],
])
def test_new_error_if_directory_with_name_exists(tmp_empty, method, kind):
    getattr(Path('env'), method)()

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteConfig.new('soopervisor.yaml', 'env')

    expected = (f"A {kind} named 'env' already exists in the "
                "current working directory, select another name "
                "for the target environment and try again.")
    assert str(excinfo.value) == expected


def test_new_creates_file_if_empty_directory(tmp_empty):
    ConcreteConfig.new('soopervisor.yaml', 'some_env')

    data = load_config()
    assert data['some_env']['backend'] == 'backend-value'
    assert data['some_env']['default'] == 'value'


def test_new_creates_section_if_existing_file(tmp_empty):
    Path('soopervisor.yaml').write_text("""
another_env:
  key: value
""")

    ConcreteConfig.new('soopervisor.yaml', 'some_env')

    data = load_config()
    assert data['some_env']['backend'] == 'backend-value'
    assert data['some_env']['default'] == 'value'


def test_new_error_if_name_already_exists(tmp_empty):
    Path('soopervisor.yaml').write_text("""
another_env:
  key: value
""")

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteConfig.new('soopervisor.yaml', 'another_env')

    expected = (
        "A target environment named 'another_env' already "
        "exists in 'soopervisor.yaml', select another name and try again.")
    assert str(excinfo.value) == expected


def test_docker_config_pass_exclude(tmp_empty):
    ConcreteDockerConfig.new('soopervisor.yaml',
                             'some_env',
                             exclude=['some-dir'])

    data = load_config()

    assert data['some_env']['exclude'] == ['some-dir']


def test_concrete_config_pass_property(tmp_empty):
    ConcreteConfig.new('soopervisor.yaml', 'some_env', default='hello')

    data = load_config()

    assert data['some_env']['default'] == 'hello'


def test_new_doesnt_save_changes_if_validation_fails(tmp_empty):

    with pytest.raises(ValidationError):
        ConcreteConfig.new('soopervisor.yaml', 'some_env', invalid='value')

    assert not Path('soopervisor.yaml').exists()


@pytest.mark.parametrize('content', ['', '- a\n- b'])
def test_error_if_not_a_mapping(tmp_empty, content):
    Path('soopervisor.yaml').write_text(content)

    with pytest.raises(ConfigurationFileTypeError):
        ConcreteConfig.load('soopervisor.yaml', 'some_env')


def test_error_if_section_is_not_a_mapping(tmp_empty):
    Path('soopervisor.yaml').write_text("""
some_env: [1, 2, 3]
""")

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteConfig.load('soopervisor.yaml', 'some_env')

    expected = ("Expected key 'some_env' in 'soopervisor.yaml' to contain "
                "a dictionary, got list")

    assert str(excinfo.value) == expected


@pytest.mark.parametrize('CLASS_', [
    ConcreteConfig,
    ConcreteDockerConfig,
])
def test_error_if_missing_backend_key_in_soopervisor(CLASS_, tmp_empty):
    Path('soopervisor.yaml').write_text(yaml.safe_dump({'some_env': {}}))

    with pytest.raises(ConfigurationError) as excinfo:
        CLASS_.load('soopervisor.yaml', 'some_env')

    assert ("Missing 'backend' key for section 'some_env' "
            "in 'soopervisor.yaml'. Add it and try again.") == str(
                excinfo.value)


def test_error_if_invalid_backend_value(tmp_empty):
    Path('soopervisor.yaml').write_text('some_env:\n    backend: wrong-value')

    with pytest.raises(ConfigurationError) as excinfo:
        ConcreteDockerConfig.load('soopervisor.yaml', 'some_env')

    expected = ("Invalid backend key for section 'some_env' in "
                "soopervisor.yaml. Expected 'backend-value', "
                "actual 'wrong-value'")
    assert str(excinfo.value) == expected


def test_returned_values():
    Path('soopervisor.yaml').write_text("""
env:
  backend: backend-value
""")

    config = ConcreteDockerConfig.load('soopervisor.yaml', 'env')

    assert config.dict() == {
        'exclude': None,
        'include': None,
        'preset': None,
        'repository': None
    }
