from faker import Faker
import os
import tempfile
import shutil
from pathlib import Path

import pytest

from ploomberci import git


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
def tmp_sample_project():
    old = os.getcwd()
    tmp = Path(tempfile.mkdtemp(), 'sample_project')
    sample_project = _path_to_tests() / 'assets' / 'sample_project'
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    shutil.rmtree(str(tmp))
    os.chdir(old)


def fake_get_git_hash(project_root):
    return 'GIT-HASH'


@pytest.fixture
def mock_git_hash(monkeypatch):
    monkeypatch.setattr(git, 'get_git_hash', fake_get_git_hash)
