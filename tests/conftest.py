from faker import Faker
import os
import tempfile
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
def tmp_directory():
    old = os.getcwd()
    tmp = tempfile.mkdtemp()
    os.chdir(str(tmp))

    yield str(Path(tmp).resolve())

    shutil.rmtree(str(tmp))
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


@pytest.fixture
def git_hash(monkeypatch):
    monkeypatch.setattr(GitRepo, "get_git_hash", lambda *args: 'GIT-HASH')
