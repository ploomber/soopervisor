from pathlib import Path
from io import StringIO
from datetime import datetime
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


def test_default_values(session_sample_project):
    config = ScriptConfig()

    assert config.paths.project == session_sample_project
    assert config.paths.products == str(Path(session_sample_project, 'output'))
    assert config.paths.environment == str(
        Path(session_sample_project, 'environment.yml'))
    assert not config.lazy_import


def test_init_from_empty_file(tmp_sample_project):
    Path('soopervisor.yaml').write_text('some_env:')

    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env')

    assert config.paths.project == str(tmp_sample_project)
    assert config.paths.products == str(Path(tmp_sample_project, 'output'))
    assert config.paths.environment == str(
        Path(tmp_sample_project, 'environment.yml'))
    assert not config.lazy_import


def test_defult_values_with_storage_enable(session_sample_project,
                                           monkeypatch):

    mock_datetime = Mock()
    mock_datetime.now.return_value = datetime(2020, 1, 1)
    monkeypatch.setattr(base_config, 'datetime', mock_datetime)

    config = ScriptConfig(storage={'provider': 'local'})

    assert config.storage.path == 'runs/2020-01-01T00:00:00'


def test_initialize_from_empty_project(session_sample_project):
    # must initialize with default values
    assert ScriptConfig.from_file_with_root_key(
        'soopervisor.yaml', env_name='some_env') == ScriptConfig()


@pytest.mark.parametrize(
    'config',
    [
        # no soopervisor.yaml
        False,
        # soopervisor.yaml with this content
        dict(paths=dict(project='.')),
        dict(paths=dict(products='output')),
        dict(cache_env=False),
    ])
def test_initialize_from_custom_path(config, tmp_sample_project_in_subdir):
    if config:
        Path('subdir',
             'soopervisor.yaml').write_text(yaml.dump({'some_env': config}))

    config = ScriptConfig.from_file_with_root_key('subdir/soopervisor.yaml',
                                                  env_name='some_env',
                                                  validate=False)
    assert config.paths.project == str(Path('.').resolve())


def test_error_if_custom_path_and_absolute_path_in_config(
        tmp_sample_project_in_subdir):
    config = dict(some_env=dict(paths=dict(project='/absolute/path')))
    Path('subdir', 'soopervisor.yaml').write_text(yaml.dump(config))

    with pytest.raises(ValueError) as excinfo:
        ScriptConfig.from_file_with_root_key('subdir/soopervisor.yaml',
                                             env_name='some_env',
                                             validate=False)

    error = (
        "Relative paths in paths.project are not allowed when "
        "initializing a project that is not in the current "
        "working directory. Edit paths.project in subdir/soopervisor.yaml "
        "and change the current value ('/absolute/path') to a relative path")
    assert str(excinfo.value) == error


def test_change_project_root(session_sample_project):
    config = ScriptConfig()
    config_new = config.with_project_root('/mnt/volume/project')

    assert config_new.paths.project == '/mnt/volume/project'
    assert config_new.paths.products == '/mnt/volume/project/output'
    assert (
        config_new.paths.environment == '/mnt/volume/project/environment.yml')


def test_initialize_with_config_file(git_hash, tmp_empty):
    d = {
        'env_name': {
            'paths': {
                'products': 'some/directory/'
            },
            'storage': {
                'provider': 'local',
                'path': 'dir-name/{{git}}'
            }
        }
    }
    Path('soopervisor.yaml').write_text(yaml.dump(d))

    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  'env_name',
                                                  validate=False)

    assert Path(config.paths.products) == Path('some/directory/').resolve()
    assert config.storage.path == 'dir-name/GIT-HASH'


def test_save_script(tmp_sample_project, monkeypatch):
    config = ScriptConfig()
    config.save_script()

    assert Path(config.paths.project, 'script.sh').exists()


@pytest.mark.parametrize('args', [
    '',
    '--entry-point .',
])
def test_ploomber_command_args_in_script(args, session_sample_project):
    config = ScriptConfig(args=args)
    assert ('ploomber build ' + args).strip() in config.to_script()


def test_custom_command(session_sample_project):
    config = ScriptConfig()
    assert 'some custom command' in config.to_script(
        command='some custom command')


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_products(create_directory, tmp_sample_project):
    config = ScriptConfig()

    if create_directory:
        Path(config.paths.products).mkdir()

    config.clean_products()


@pytest.mark.parametrize('project_root, product_root, expected', [
    ['/', 'output', '/output'],
    ['/project', '/path/to/output', '/path/to/output'],
])
def test_converts_product_root_to_absolute(project_root, product_root,
                                           expected, monkeypatch):
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
def test_converts_path_to_env_to_absolute(project_root, path_to_environment,
                                          expected, monkeypatch,
                                          tmp_sample_project):
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
def test_converts_environment_prefix_to_absolute(project_root, prefix,
                                                 expected, monkeypatch):
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
        yaml.dump({'env_name': {
            'environment_prefix': prefix
        }}))
    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env',
                                                  validate=False)
    assert config.environment_name == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'sample-project-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_conda_activate_line_in_script(prefix, expected, tmp_sample_project):
    d = {'environment_prefix': prefix}
    Path('soopervisor.yaml').write_text(yaml.dump({'some_env': d}))
    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env',
                                                  validate=False)
    script = config.to_script()

    assert f'conda activate {expected}' in script
