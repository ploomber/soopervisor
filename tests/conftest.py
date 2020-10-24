from faker import Faker
import os
import shutil
from pathlib import Path

import pytest

from soopervisor.git_handler import GitRepo


def _path_to_tests():
    return Path(__file__).absolute().parent


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture()
def tmp_empty(tmp_path):
    old = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(Path(tmp_path).resolve())
    os.chdir(old)


@pytest.fixture()
def tmp_sample_project(tmp_path):
    relative_path_project = "assets/sample_project"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    sample_project = _path_to_tests() / relative_path_project
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    os.chdir(old)


@pytest.fixture(scope='session')
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


@pytest.fixture
def git_hash(monkeypatch):
    monkeypatch.setattr(GitRepo, "get_git_hash", lambda *args: 'GIT-HASH')
