import subprocess
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest

from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def test_run_script(git_hash, monkeypatch, tmp_sample_project):
    script_config = ScriptConfig(paths={'project': str(tmp_sample_project)})
    executor = LocalExecutor(script_config)

    mock_subprocess = Mock()
    mock_shutil = Mock()

    with monkeypatch.context() as m:
        m.setattr(subprocess, 'run', value=mock_subprocess)
        m.setattr(shutil, 'copytree', value=mock_shutil)
        executor.execute()

    # must execute from the project's root
    expected_location = Path(tmp_sample_project, 'script.sh')

    # deletes upon execution
    assert not expected_location.exists()
    mock_subprocess.assert_called_once_with(
        ['bash', str(expected_location)], check=True)


def test_error_run_script(git_hash, monkeypatch, tmp_sample_project):
    script_config = ScriptConfig()
    executor = LocalExecutor(script_config)
    expected_location = Path(tmp_sample_project, 'script.sh')

    mock_subprocess = Mock(side_effect=Exception)
    mock_shutil = Mock()

    with pytest.raises(Exception), monkeypatch.context() as m:
        m.setattr(subprocess, 'run', value=mock_subprocess)
        m.setattr(shutil, 'copytree', value=mock_shutil)
        executor.execute()

    assert not expected_location.exists()
    mock_subprocess.assert_called_once_with(
        ['bash', str(expected_location)], check=True)
    mock_shutil.assert_not_called()
