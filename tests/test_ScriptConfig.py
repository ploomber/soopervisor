import yaml
from pathlib import Path
from io import StringIO

import pytest

from soopervisor.script import ScriptConfig as script_config_module
from soopervisor.script.ScriptConfig import ScriptConfig, Paths


def test_default_values(git_hash, tmp_directory):
    config = ScriptConfig().dict()

    assert config['paths']['project'] == tmp_directory
    assert config['paths']['products'] == str(Path(tmp_directory, 'output'))
    assert config['paths']['environment'] == str(
        Path(tmp_directory, 'environment.yml'))


def test_on_update(git_hash, tmp_directory):
    config = ScriptConfig()

    config.paths.project = 'new_project_root'
    proj = Path('new_project_root')
    proj.mkdir()
    (proj / 'environment.yml').write_text(yaml.dump({'name': 'some-env'}))

    d = config.dict()
    new_root = Path(tmp_directory, 'new_project_root')
    assert d['paths']['project'] == str(new_root)
    assert d['paths']['environment'] == str(Path(new_root, 'environment.yml'))
    assert d['paths']['products'] == str(Path(new_root, 'output'))


def test_initialize_from_empty_project(git_hash, tmp_directory):
    # must initialize with default values
    assert ScriptConfig.from_path('.') == ScriptConfig()


def test_initialize_with_config_file(git_hash, tmp_directory):
    d = {
        'paths': {
            'products': 'some/directory/'
        },
        'storage': {
            'provider': 'local',
            'path': 'dir-name/{{git}}'
        }
    }
    Path(tmp_directory, 'soopervisor.yaml').write_text(yaml.dump(d))

    config = ScriptConfig.from_path('.').dict()

    assert Path(
        config['paths']['products']) == Path('some/directory/').resolve()
    assert config['storage']['path'] == 'dir-name/GIT-HASH'


def test_save_script(git_hash, tmp_directory):
    config = ScriptConfig()
    config.save_script()
    assert Path(config.paths.project, 'script.sh').exists()


@pytest.mark.parametrize('args', [
    '',
    '--entry-point .',
])
def test_ploomber_command_args_in_script(args, git_hash, tmp_directory):
    config = ScriptConfig(args=args)
    assert 'ploomber build ' + args in config.to_script()


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_products(git_hash, create_directory, tmp_directory):
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

    monkeypatch.setattr(script_config_module, 'open', _open, raising=False)

    d = ScriptConfig(
        paths=dict(project=project_root, products=product_root)).dict()

    assert d['paths']['products'] == expected


@pytest.mark.parametrize('project_root, path_to_environment, expected', [
    ['/', 'environment.yml', '/environment.yml'],
    ['/project', '/path/to/environment.yml', '/path/to/environment.yml'],
])
def test_convers_path_to_env_to_absolute(git_hash, project_root,
                                         path_to_environment, expected,
                                         monkeypatch):
    def _open(path):
        return StringIO(yaml.dump({'name': 'some-env'}))

    monkeypatch.setattr(script_config_module, 'open', _open, raising=False)

    config = ScriptConfig(
        paths=dict(project=project_root, environment=path_to_environment))
    d = config.dict()
    expected_line = (f'conda env create --file {expected}')

    assert d['paths']['environment'] == expected
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

    monkeypatch.setattr(script_config_module, 'open', _open, raising=False)

    d = ScriptConfig(paths=dict(project=project_root),
                     environment_prefix=prefix).dict()

    assert d['environment_prefix'] == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'some-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_environment_name(prefix, expected, tmp_directory):
    Path(tmp_directory, 'soopervisor.yaml').write_text(
        yaml.dump({'environment_prefix': prefix}))
    config = ScriptConfig.from_path('.')
    d = config.dict()
    assert d['environment_name'] == expected


@pytest.mark.parametrize('prefix, expected', [
    [None, 'some-env'],
    ['/some/prefix', '/some/prefix'],
])
def test_conda_activate_line_in_script(prefix, expected, tmp_directory):
    d = {'environment_prefix': prefix}
    Path(tmp_directory, 'soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_path(tmp_directory)
    script = config.to_script()

    assert f'conda activate {expected}' in script


def test_script_does_not_upload_if_empty_provider(tmp_directory):
    d = {'storage': {'provider': None}}
    Path(tmp_directory, 'soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_path('.')
    script = config.to_script()
    assert 'soopervisor upload' not in script


@pytest.mark.parametrize('provider', ['local', 'box'])
def test_script_uploads_if_provider(git_hash, provider, tmp_directory):
    d = {'storage': {'provider': provider}}
    Path(tmp_directory, 'soopervisor.yaml').write_text(yaml.dump(d))
    config = ScriptConfig.from_path('.')
    script = config.to_script()
    assert 'soopervisor upload' in script


@pytest.mark.xfail
def test_error_if_missing_environment_yml():
    # TODO: add custom errror when missing conda spec file
    raise NotImplementedError
