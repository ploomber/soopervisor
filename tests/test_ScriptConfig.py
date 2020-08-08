from pathlib import Path

from ploomberci.script.ScriptConfig import ScriptConfig


def test_initialize_from_empty_project_root(tmp_directory):
    config = ScriptConfig.from_path('.')
    assert config


def test_save_script(tmp_directory):
    config = ScriptConfig.from_path('.')
    config.save_script()
    assert Path('script.sh').exists()
