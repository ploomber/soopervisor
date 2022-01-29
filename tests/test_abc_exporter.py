import yaml
import os
from pathlib import Path

import pytest
from ploomber.exceptions import DAGSpecInvalidError
from click import ClickException

from soopervisor.abc import (AbstractExporter, AbstractConfig,
                             AbstractDockerConfig)
from soopervisor import exceptions


class ConcreteConfig(AbstractConfig):
    default: str = 'value'

    @classmethod
    def get_backend_value(self):
        return 'backend-value'

    @classmethod
    def get_presets(cls):
        return ('preset', )


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


class ConcreteDockerConfig(AbstractDockerConfig):

    @classmethod
    def get_backend_value(self):
        return 'backend-value'


class ConcreteDockerExporter(AbstractExporter):
    CONFIG_CLASS = ConcreteDockerConfig

    @staticmethod
    def _add(cfg, env_name):
        pass

    @staticmethod
    def _export():
        pass

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass


@pytest.mark.parametrize('method', ['new', 'load'])
def test_error_if_missing_environment_lock_yml(method, tmp_sample_project):
    Path('environment.lock.yml').unlink()

    with pytest.raises(ClickException) as excinfo:
        getattr(ConcreteExporter, method)('soopervisor.yaml',
                                          env_name='some_env')

    assert 'Expected requirements.lock.txt or environment.lock.yml' in str(
        excinfo.value)
    assert not Path('soopervisor.yaml').exists()


@pytest.mark.parametrize('method', ['new', 'load'])
def test_error_if_dag_fails_to_initialize(method, tmp_sample_project):
    Path('pipeline.yaml').unlink()

    with pytest.raises(DAGSpecInvalidError) as excinfo:
        getattr(ConcreteExporter, method)('soopervisor.yaml',
                                          env_name='some_env')

    assert 'Could not find dag spec with name pipeline.yaml' in str(
        excinfo.value)


# TODO: finish this
def test_initializes_pipeline_with_name_if_exists(tmp_sample_project):
    os.rename('pipeline.yaml', 'pipeline.serve.yaml')

    assert ConcreteExporter.new('soopervisor.yaml', env_name='serve')


def test_load_error_if_missing_env_name(tmp_sample_project):
    Path('soopervisor.yaml').write_text("""
env:
    key: value
""")

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        ConcreteExporter.load('soopervisor.yaml', env_name='some_env')

    expected = ("'soopervisor.yaml' does not contain a target "
                "environment named 'some_env'")
    assert str(excinfo.value) == expected


def test_new_error_if_name_already_exists(tmp_sample_project):
    Path('soopervisor.yaml').write_text("""
env:
    key: value
""")

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        ConcreteExporter.new('soopervisor.yaml', env_name='env')

    expected = ("A target environment named 'env' already exists in "
                "'soopervisor.yaml', select another name and try again.")
    assert str(excinfo.value) == expected


def test_new_includes_product_prefixes_in_docker_config(tmp_sample_project):
    Path('pipeline.yaml').write_text("""
tasks:
  - source: raw.py
    name: raw
    product:
      nb: products/nb.ipynb
      data: products/data.csv
""")

    ConcreteDockerExporter.new('soopervisor.yaml', env_name='env')

    with Path('soopervisor.yaml').open() as f:
        d = yaml.safe_load(f)

    assert d['env']['exclude'] == ['products']


def test_new_doesn_include_product_prefixes(tmp_sample_project):
    Path('pipeline.yaml').write_text("""
tasks:
  - source: raw.py
    name: raw
    product:
      nb: products/nb.ipynb
      data: products/data.csv
""")

    ConcreteConfig.new('soopervisor.yaml', env_name='env')

    with Path('soopervisor.yaml').open() as f:
        d = yaml.safe_load(f)

    assert d['env'] == {'backend': 'backend-value'}


def test_new_pass_preset(tmp_sample_project):
    ConcreteExporter.new('soopervisor.yaml', env_name='env', preset='preset')

    with Path('soopervisor.yaml').open() as f:
        d = yaml.safe_load(f)

    assert d['env']['preset'] == 'preset'
