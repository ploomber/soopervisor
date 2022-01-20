import importlib
import tempfile
import sys
import subprocess
from faker import Faker
import os
import shutil
from pathlib import Path
from copy import copy
from unittest.mock import Mock

import my_project
import pytest
from ploomber.io import _commander, _commander_tester
from ploomber.telemetry import telemetry

from soopervisor import commons


def _mock_docker_calls(monkeypatch, cmd, proj, tag):
    """
    Mock subprocess calls made by ploomber.io._commander.Commander (which
    is used interally by the soopervisor.commons.docker module).

    This allows us to prevent actual CLI calls to "docker run". Instead, we
    mock the call and return a value. However, this function will allow calls
    to "python -m build --sdist" to pass. For details, see the CommanderTester
    docstring in the ploomber package.
    """
    tester = _commander_tester.CommanderTester(
        run=[
            ('python', '-m', 'build', '--sdist'),
        ],
        return_value={
            ('docker', 'run', f'{proj}:{tag}', 'python', '-c', cmd): b'True\n'
        })

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)

    return tester


def _path_to_tests():
    return Path(__file__).absolute().parent


@pytest.fixture
def ignore_ploomber_stats_enabled_env_var(monkeypatch):
    """
    GitHub Actions configuration scripts set the PLOOMBER_STATS_ENABLED
    environment variable to prevent CI events from going to posthog, this
    inferes with some tests. This fixture removes its value temporarily
    """
    monkeypatch.delenv('PLOOMBER_STATS_ENABLED', raising=True)


@pytest.fixture
def ignore_env_var_and_set_tmp_default_home_dir(
        tmp_empty, ignore_ploomber_stats_enabled_env_var, monkeypatch):
    """
    ignore_ploomber_stats_enabled_env_var + overrides DEFAULT_HOME_DIR
    to prevent the local configuration to interfere with tests
    """
    monkeypatch.setattr(telemetry, 'DEFAULT_HOME_DIR', '.')


@pytest.fixture
def root_path():
    return _path_to_tests().parent


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture
def tmp_empty(tmp_path):
    old = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(Path(tmp_path).resolve())
    os.chdir(old)


@pytest.fixture
def tmp_sample_project(tmp_path):
    relative_path_project = "assets/sample_project"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    sample_project = _path_to_tests() / relative_path_project
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    os.chdir(old)


@pytest.fixture
def tmp_fast_pipeline(tmp_path):
    relative_path_project = "assets/fast-pipeline"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    fast_pipeline = _path_to_tests() / relative_path_project
    shutil.copytree(str(fast_pipeline), str(tmp))

    os.chdir(str(tmp))
    Path('environment.yml').touch()

    yield tmp

    os.chdir(old)


@pytest.fixture
def backup_packaged_project():
    old = os.getcwd()

    backup = tempfile.mkdtemp()
    root = Path(my_project.__file__).parents[2]

    # sanity check, in case we change the structure
    assert root.name == 'my_project'

    shutil.copytree(str(root), str(Path(backup, 'my_project')))

    pkg_root = str(
        Path(importlib.util.find_spec('my_project').origin).parents[2])
    os.chdir(str(pkg_root))

    yield

    os.chdir(old)

    shutil.rmtree(str(root))
    shutil.copytree(str(Path(backup, 'my_project')), str(root))
    shutil.rmtree(backup)


@pytest.fixture
def tmp_sample_project_in_subdir(tmp_sample_project):
    """
    Sample as tmp_sample_project but moves all contents to a subdirectory
    """
    files = os.listdir()
    sub_dir = Path('subdir')
    sub_dir.mkdir()

    for f in files:
        Path(f).rename(sub_dir / f)

    yield tmp_sample_project


@pytest.fixture
def tmp_callables(tmp_path):
    """Pipeline with PythonCallable tasks
    """
    relative_path = "assets/callables"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path)
    sample_project = _path_to_tests() / relative_path
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    os.chdir(old)


@pytest.fixture
def session_sample_project(tmp_path_factory):
    """
    Similar to tmp_directory but tasks should not modify content, since
    it's a session-wide fixture
    """
    sample_project = str(_path_to_tests() / 'assets' / 'sample_project')
    tmp_dir = tmp_path_factory.mktemp('session-wide-tmp-directory')
    tmp_target = str(tmp_dir / 'sample_project')

    shutil.copytree(sample_project, tmp_target)
    old = os.getcwd()
    os.chdir(tmp_target)

    yield tmp_target

    # TODO: check files were not modified

    os.chdir(old)


@pytest.fixture(scope='session')
def download_projects(tmpdir_factory):
    tmp_path = tmpdir_factory.mktemp('projects')
    subprocess.run([
        'git',
        'clone',
        'https://github.com/ploomber/projects',
        str(tmp_path),
    ],
                   check=True)
    yield str(Path(tmp_path).resolve())


@pytest.fixture
def tmp_projects(download_projects, tmp_path):
    old = os.getcwd()
    target = tmp_path / 'projects'
    shutil.copytree(download_projects, target)
    os.chdir(str(target))
    yield str(Path(target).resolve())
    os.chdir(old)


@pytest.fixture
def no_sys_modules_cache():
    """
    Removes modules from sys.modules that didn't exist before the test
    """
    mods = set(sys.modules)

    yield

    current = set(sys.modules)

    to_remove = current - mods

    for a_module in to_remove:
        del sys.modules[a_module]


@pytest.fixture
def add_current_to_sys_path():
    old = copy(sys.path)
    sys.path.insert(0, os.path.abspath('.'))
    yield sys.path
    sys.path = old


@pytest.fixture
def skip_repo_validation(monkeypatch):
    # do not validate repository (using the default value will raise an error)
    monkeypatch.setattr(commons.docker, '_validate_repository', lambda x: x)
