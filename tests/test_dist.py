"""
Test generated wheel
"""
import tarfile
from glob import iglob
from pathlib import Path
import shutil
import os
import subprocess
import zipfile

import pytest


def files_in_directory(path, exclude_pyc=True):
    path = Path(path)
    files = [
        str(Path(f).relative_to(path))
        for f in iglob(str(path / '**'), recursive=True)
        if '__pycache__' not in f
    ]

    if exclude_pyc:
        files = [f for f in files if '.pyc' not in f]

    return files


def assert_same_files(reference, directory):
    expected = set(files_in_directory(reference))
    existing = set(files_in_directory(directory))

    missing = expected - existing
    extra = existing - expected

    if missing:
        raise ValueError(f'missing files: {missing}')

    if extra:
        raise ValueError(f'extra files: {extra}')


def extract_zip(path, tmp_path):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(tmp_path)


def extract_tar(path, tmp_path):
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(tmp_path)


def get_dir_name(tmp_path):
    if any('.dist-info' in f for f in os.listdir(tmp_path)):
        # wheel
        return Path(tmp_path, 'soopervisor', 'assets')
    else:
        # source dist
        dir_name = os.listdir(tmp_path)[0]
        return Path(tmp_path, dir_name, 'src', 'soopervisor', 'assets')


@pytest.mark.parametrize(
    'fmt, extractor',
    [
        ['bdist_wheel', extract_zip],
        ['sdist', extract_tar],
    ],
)
def test_dist(fmt, extractor, tmp_path):
    """Make sure the wheel does not contain stuff it shouldn't have
    """
    if Path('build').exists():
        shutil.rmtree('build')

    if Path('dist').exists():
        shutil.rmtree('dist')

    subprocess.run(['python', 'setup.py', fmt], check=True)
    extractor(Path('dist', os.listdir('dist')[0]), tmp_path)

    path_dist = get_dir_name(tmp_path)
    path_local = Path('src', 'soopervisor', 'assets')

    # no pycache files
    assert not [
        f for f in files_in_directory(path_dist, exclude_pyc=False)
        if '.pyc' in f
    ]

    # therest should be there
    assert_same_files(reference=path_local, directory=path_dist)
