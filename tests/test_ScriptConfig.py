from pathlib import Path
from io import StringIO
from unittest.mock import Mock

import yaml
import pytest
from pydantic import ValidationError

import soopervisor.base.config as base_config
from soopervisor.base.config import ScriptConfig, StorageConfig, Paths


@pytest.mark.parametrize('class_', [ScriptConfig, StorageConfig, Paths])
def test_models_fail_when_passing_extra_args(class_):
    kwargs = dict(extra=1)

    # special case, StorageConfig needs a paths arg
    if class_ is StorageConfig:
        kwargs['paths'] = None

    with pytest.raises(ValidationError):
        class_(**kwargs)


def test_default_values(git_hash, session_sample_project):
    config = ScriptConfig()

    assert config.paths.project == session_sample_project
    assert config.paths.products == str(Path(session_sample_project, 'output'))
    assert config.paths.environment == str(
        Path(session_sample_project, 'environment.yml'))
    assert not config.lazy_import


def test_initialize_from_empty_project(git_hash):
    # must initialize with default values
    assert ScriptConfig.from_project('.') == ScriptConfig()


def test_initialize_from_custom_path(tmp_sample_project_in_subdir):
    sub_dir = Path('subdir')

    # initialize with a custom path
    config = ScriptConfig.from_project('subdir', validate=False)

    # project path should be located in the custom path
    assert config.paths.project == str(sub_dir.resolve())


def test_initialize_with_config_file(git_hash, tmp_empty):
    d = {
        'paths': {
            'products': 'some/directory/'
        },
        'storage': {
            'provider': 'local',
            'path': 'dir-name/{{git}}'
        }
    }
    Path('soopervisor.yaml').write_text(yaml.dump(d))

    config = ScriptConfig.from_project('.', validate=False)

    assert Path(config.paths.products) == Path('some/directory/').resolve()
    assert config.storage.path == 'dir-name/GIT-HASH'


def test_save_script(git_hash, tmp_sample_project, monkeypatch):
    config = ScriptConfig()
    config.save_script()

    assert Path(config.paths.project, 'script.sh').exists()


@pytest.mark.parametrize('args', [
    '',
    '--entry-point .',
])
def test_ploomber_command_args_in_script(args, git_hash,
                                         session_sample_project):
    config = ScriptConfig(args=args)
    assert 'ploomber build ' + args in config.to_script()


def test_custom_command(session_sample_project):
    config = ScriptConfig()
    assert 'some custom command' in config.to_script(
        command='some custom command')


def test_error_if_custom_command_and_args(session_sample_project):
    config = ScriptConfig(args='some args')

    with pytest.raises(ValueError) as excinfo:
        config.to_script(command='some custom command')

    assert 'args should be empty (got "some args")' in str(excinfo.value)


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_products(git_hash, create_directory, tmp_sample_project):
    config = ScriptConfig()

    if create_directory:
        Path(config.paths.products).mkdir()

    config.clean_products()


@pytest.mark.parametrize('project_root, product_root, expected', [
    ['/', 'output', '/output'],
    ['/project', '/path/to/output', '/path/to/output'],
])
def test_converts_product_root_to_absolute(git_hash, project_root,
                                           product_root, expected,
                                           monkeypatch):
    def _open(path):
        return StringIO(yaml.dump({'name': 'some-env'}))

    monkeypatch.setattr(base_config, 'open', _open, raising=False)

    config = ScriptConfig(
        paths=dict(project=project_root, products=product_root))

    assert config.paths.products == expected


@pytest.mark.parametrize('project_root, path_to_environment, expected', [
    ['/', 'environment.yml', '/environment.yml'],
    ['/project', '/path/to/environment.yml', '/path/to/environment.yml'],
])
def test_converts_path_to_env_to_absolute(git_hash, project_root,
                                          path_to_environment, expected,
                                          monkeypatch, tmp_sample_project):
    def _open(path):
        return StringIO(yaml.dump({'name': 'some-env'}))

    monkeypatch.setattr(base_config, 'open', _open, raising=False)

    config = ScriptConfig(
        paths=dict(project=project_root, environment=path_to_environment))
    expected_line = (f'conda env create --file {expected}')

    assert config.paths.environment == expected
    assert expected_line in config.to_script()


@pytest.mark.parametrize('project_root, prefix, expected', [
    ['/', 'prefix', '/prefix'],
    ['/project', '/path/to/prefix', '/path/to/prefix'],
])
def test_converts_environment_prefix_to_absolute(git_hash, project_root,
                                                 prefix, expected,
                                                 monkeypatch):
    def _open(path):
        return StringIO(yaml.dump({'name': 'some-env'}))

    monkeypatch.setattr(base_config, 'open', _open, raising=False)

    config = ScriptConfig(paths=dict(project=project_root),
                          environment_prefix=prefix)

    assert config.environment_prefix == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'sample-project-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_environment_name(prefix, expected, tmp_sample_project):
    Path('soopervisor.yaml').write_text(
        yaml.dump({'environment_prefix': prefix}))
    config = ScriptConfig.from_project('.')
    assert config.environment_name == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'sample-project-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_conda_activate_line_in_script(prefix, expected, tmp_sample_project):
    d = {'environment_prefix': prefix}
    Path('soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_project('.', validate=False)
    script = config.to_script()

    assert f'conda activate {expected}' in script


def test_script_does_not_upload_if_empty_provider(tmp_sample_project):
    d = {'storage': {'provider': None}}
    Path('soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_project('.', validate=False)
    script = config.to_script()
    assert 'soopervisor upload' not in script


@pytest.mark.parametrize('provider', ['local', 'box'])
def test_script_uploads_if_provider(git_hash, provider, tmp_sample_project):
    d = {'storage': {'provider': provider}}
    Path('soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_project('.', validate=False)
    script = config.to_script()
    assert 'soopervisor upload' in script


@pytest.mark.xfail
def test_error_if_missing_environment_yml():
    # TODO: add custom errror when missing conda spec file
    raise NotImplementedError
