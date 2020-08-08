from pathlib import Path

import pytest

from ploomberci.script.ScriptConfig import ScriptConfig


def test_default_values(mock_git_hash, tmp_directory):
    config = ScriptConfig()

    assert config.project_root == tmp_directory
    assert config.product_root == str(Path(tmp_directory, 'output'))
    assert config.path_to_environment == str(
        Path(tmp_directory, 'environment.yml'))
    assert config.box.upload_path == 'projects/GIT-HASH'


def test_initialize_from_empty_project_root(mock_git_hash, tmp_directory):
    config = ScriptConfig.from_path('.')
    assert config


def test_save_script(mock_git_hash, tmp_directory):
    config = ScriptConfig.from_path('.')
    config.save_script()
    assert Path('script.sh').exists()


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_product_root(mock_git_hash, create_directory, tmp_directory):
    config = ScriptConfig.from_path('.')

    if create_directory:
        Path(config.product_root).mkdir()

    config.clean_product_root()
