from pathlib import Path

import pytest

from ploomberci.script.ScriptConfig import ScriptConfig


def test_default_values(mock_git_hash, tmp_directory):
    config = ScriptConfig()

    assert config.paths.project == tmp_directory
    assert config.paths.products == str(Path(tmp_directory, 'output'))
    assert config.paths.environment == str(
        Path(tmp_directory, 'environment.yml'))
    assert config.storage.path == 'projects/GIT-HASH'


def test_initialize_from_empty_project(mock_git_hash, tmp_directory):
    config = ScriptConfig.from_path('.')
    assert config


def test_save_script(mock_git_hash, tmp_directory):
    config = ScriptConfig.from_path('.')
    config.save_script()
    assert Path('script.sh').exists()


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_products(mock_git_hash, create_directory, tmp_directory):
    config = ScriptConfig.from_path('.')

    if create_directory:
        Path(config.paths.products).mkdir()

    config.clean_products()
