from pathlib import Path
from io import StringIO

import yaml
import pytest
from pydantic import ValidationError

import soopervisor.base.config as base_config
from soopervisor.base.config import ScriptConfig, Paths


@pytest.mark.parametrize('class_', [ScriptConfig, Paths])
def test_models_fail_when_passing_extra_args(class_):
    kwargs = dict(extra=1)

    with pytest.raises(ValidationError):
        class_(**kwargs)


def test_default_values(session_sample_project):
    config = ScriptConfig()

    assert config.paths.project == session_sample_project
    assert config.paths.environment == str(
        Path(session_sample_project, 'environment.yml'))
    assert not config.lazy_import


def test_init_from_empty_file(tmp_sample_project):
    Path('soopervisor.yaml').write_text('some_env:')

    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env')

    assert config.paths.project == str(tmp_sample_project)
    assert config.paths.environment == str(
        Path(tmp_sample_project, 'environment.yml'))
    assert not config.lazy_import


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
        dict(cache_env=False),
    ])
def test_initialize_from_custom_path(config, tmp_sample_project_in_subdir):
    if config:
        Path('subdir',
             'soopervisor.yaml').write_text(yaml.dump({'some_env': config}))

    config = ScriptConfig.from_file_with_root_key('subdir/soopervisor.yaml',
                                                  env_name='some_env')
    assert config.paths.project == str(Path('subdir').resolve())


def test_error_if_custom_path_and_absolute_path_in_config(
        tmp_sample_project_in_subdir):
    config = dict(some_env=dict(paths=dict(project='/absolute/path')))
    Path('subdir', 'soopervisor.yaml').write_text(yaml.dump(config))

    with pytest.raises(ValueError) as excinfo:
        ScriptConfig.from_file_with_root_key('subdir/soopervisor.yaml',
                                             env_name='some_env')

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
    assert (
        config_new.paths.environment == '/mnt/volume/project/environment.yml')


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
        yaml.dump({'some_env': {
            'environment_prefix': prefix
        }}))
    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env')
    assert config.environment_name == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'sample-project-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_conda_activate_line_in_script(prefix, expected, tmp_sample_project):
    d = {'environment_prefix': prefix}
    Path('soopervisor.yaml').write_text(yaml.dump({'some_env': d}))
    config = ScriptConfig.from_file_with_root_key('soopervisor.yaml',
                                                  env_name='some_env')
    script = config.to_script()

    assert f'conda activate {expected}' in script
