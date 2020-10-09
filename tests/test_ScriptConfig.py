import yaml
from pathlib import Path

import pytest

from soopervisor.script.ScriptConfig import ScriptConfig


def test_default_values(git_hash, tmp_directory):
    config = ScriptConfig()

    assert config.paths.project == tmp_directory
    assert config.paths.products == str(Path(tmp_directory, 'output'))
    assert config.paths.environment == str(
        Path(tmp_directory, 'environment.yml'))
    assert config.storage.path == 'runs/GIT-HASH'


def test_initialize_from_empty_project(git_hash, tmp_directory):
    # must initialize with default values
    assert ScriptConfig.from_path('.') == ScriptConfig()


def test_initialize_with_config_file(git_hash, tmp_directory):
    d = {
        'paths': {
            'products': 'some/directory/'
        },
        'storage': {
            'path': 'dir-name/{{git}}'
        }
    }
    Path(tmp_directory, 'soopervisor.yaml').write_text(yaml.dump(d))

    config = ScriptConfig.from_path('.')

    assert Path(config.paths.products) == Path('some/directory/').resolve()
    assert config.storage.path == 'dir-name/GIT-HASH'


def test_save_script(git_hash, tmp_directory):
    config = ScriptConfig()
    config.save_script()
    assert Path('script.sh').exists()


def test_to_script(git_hash, tmp_directory):
    config = ScriptConfig()
    assert config.to_script()


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_products(git_hash, create_directory, tmp_directory):
    config = ScriptConfig()

    if create_directory:
        Path(config.paths.products).mkdir()

    config.clean_products()


@pytest.mark.parametrize('project_root, product_root, expected', [
    ['/', 'output', '/output'],
    ['/', '/path/to/output', '/path/to/output'],
])
def test_converts_product_root_to_absolute(git_hash, project_root,
                                           product_root, expected):
    config = ScriptConfig(
        paths=dict(project=project_root, products=product_root))
    assert config.paths.products == expected


@pytest.mark.parametrize('project_root, path_to_environment, expected', [
    ['/', 'environment.yml', '/environment.yml'],
    ['/', '/path/to/environment.yml', '/path/to/environment.yml'],
])
def test_convers_path_to_env_to_absolute(git_hash, project_root,
                                         path_to_environment, expected):
    config = ScriptConfig(
        paths=dict(project=project_root, environment=path_to_environment))
    expected_line = ('conda env create --file ' + expected +
                     ' --name ploomber-env --force')

    assert config.paths.environment == expected
    assert expected_line in config.to_script()
