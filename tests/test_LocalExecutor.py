from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def test_run_script(git_hash, monkeypatch, tmp_sample_project):
    mock = Mock()
    monkeypatch.setattr(subprocess, 'run', value=mock)

    script_config = ScriptConfig(paths={'project': 'my-project'})

    executor = LocalExecutor(script_config)
    executor.execute()

    # must execute from the project's root
    expected_location = Path(tmp_sample_project, 'my-project', 'script.sh')

    # deletes upon execution
    assert not expected_location.exists()
    mock.assert_called_once_with(['bash', str(expected_location)], check=True)


def test_error_run_script(git_hash, monkeypatch, tmp_sample_project):
    mock = Mock(side_effect=Exception)
    monkeypatch.setattr(subprocess, 'run', value=mock)

    script_config = ScriptConfig()

    executor = LocalExecutor(script_config)

    expected_location = Path(tmp_sample_project, 'script.sh')

    with pytest.raises(Exception):
        executor.execute()

    assert not expected_location.exists()
    mock.assert_called_once_with(['bash', str(expected_location)], check=True)
