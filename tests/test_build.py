import os

from soopervisor import build
from soopervisor.executors.LocalExecutor import LocalExecutor


def null_execute(self):
    pass


def test_build(mock_git_hash, tmp_sample_project):
    build.build_project('.', clean_products_path=False)


def test_clean_products_path(mock_git_hash, monkeypatch, tmp_sample_project):
    monkeypatch.setattr(LocalExecutor, 'execute', null_execute)
    build.build_project('.', clean_products_path=True)

    assert not len(os.listdir('output'))
