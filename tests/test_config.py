import os
from pathlib import Path

import pytest

from soopervisor import config, exceptions


def test_get_backend_error_missing_file(tmp_empty):
    with pytest.raises(exceptions.MissingConfigurationFileError):
        config.get_backend('some_name')


def test_get_backend_missing_key(tmp_empty):
    Path('soopervisor.yaml').write_text("""
env:
    backend: airflow
""")

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        config.get_backend('another_env')

    expected = ("Missing 'another_env' section "
                "in 'soopervisor.yaml'. Available ones are: 'env'")
    assert str(excinfo.value) == expected


def test_get_backend_missing_backend(tmp_empty):
    Path('soopervisor.yaml').write_text("""
env:
    key: value
""")

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        config.get_backend('env')

    expected = ("Misconfigured environment: missing 'backend' "
                "key in section 'env' in 'soopervisor.yaml'")
    assert str(excinfo.value) == expected


def test_get_backend_invalid_backend_value(tmp_empty):
    Path('soopervisor.yaml').write_text("""
env:
    backend: invalid
""")

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        config.get_backend('env')

    expected = ("Misconfigured environment: 'invalid' is not a "
                "valid backend. backend must be one of: "
                "'aws_batch', 'aws_lambda', 'argo_workflows', "
                "'airflow', 'kubeflow', 'slurm', 'cloud'")
    assert str(excinfo.value) == expected


def test_replace_env_does_not_exists(tmp_empty):
    config.replace_env('name', 'some-dir')

    assert not os.listdir()


@pytest.mark.parametrize('env_yaml_create', [False, True])
def test_replace_env(tmp_empty, env_yaml_create):
    dir_ = Path('dir')
    dir_.mkdir()

    if env_yaml_create:
        (dir_ / 'env.yaml').write_text('old content')

    (dir_ / 'env.name.yaml').write_text('new content')

    config.replace_env('name', 'dir')

    assert (dir_ / 'env.yaml').read_text() == 'new content'
