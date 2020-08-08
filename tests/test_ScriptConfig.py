from pathlib import Path

import pytest

from ploomberci.script.ScriptConfig import ScriptConfig


def test_initialize_from_empty_project_root(tmp_directory):
    config = ScriptConfig.from_path('.')
    assert config


def test_save_script(tmp_directory):
    config = ScriptConfig.from_path('.')
    config.save_script()
    assert Path('script.sh').exists()


@pytest.mark.parametrize('create_directory', [False, True])
def test_clean_product_root(create_directory, tmp_directory):
    config = ScriptConfig.from_path('.')

    if create_directory:
        Path(config.get_product_root()).mkdir()

    config.clean_product_root()