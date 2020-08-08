import os

from ploomberci import build
from ploomberci.executors.LocalExecutor import LocalExecutor


def null_execute(self):
    pass


def test_build(mock_git_hash, tmp_sample_project):
    build.build_project('.', clean_product_root=False)


def test_clean_product_root(mock_git_hash, monkeypatch, tmp_sample_project):
    monkeypatch.setattr(LocalExecutor, 'execute', null_execute)
    build.build_project('.', clean_product_root=True)

    assert not len(os.listdir('output'))
