from pathlib import Path
import os

from soopervisor import build
from soopervisor.executors.LocalExecutor import LocalExecutor


def test_build(git_hash, tmp_sample_project):
    build.build_project('.', clean_products_path=False, dry_run=False)


def test_clean_products_path(git_hash, monkeypatch, tmp_sample_project):
    monkeypatch.setattr(LocalExecutor, 'execute', lambda *args: None)
    build.build_project('.', clean_products_path=True, dry_run=False)

    assert not len(os.listdir('output')) and Path('output').is_dir()
