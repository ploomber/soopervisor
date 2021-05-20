import tarfile
import subprocess
from pathlib import Path

from soopervisor.commons import source


def git_init():
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


def test_copy(tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'another').touch()
    git_init()
    source.copy('.', 'dist')

    expected = set(
        Path(p) for p in (
            'dist',
            'dist/file',
            'dist/dir',
            'dist/dir/another',
        ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_copy_with_gitignore(tmp_empty):
    Path('file').touch()
    Path('ignoreme').touch()

    Path('.gitignore').write_text('ignoreme')
    git_init()
    source.copy('.', 'dist')

    expected = set(Path(p) for p in (
        'dist/',
        'dist/file',
    ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_include(tmp_empty):
    Path('file').touch()
    Path('secrets.txt').touch()

    Path('.gitignore').write_text('secrets.txt')
    git_init()

    source.copy('.', 'dist', include=['secrets.txt'])

    expected = set(
        Path(p) for p in (
            'dist/',
            'dist/file',
            'dist/secrets.txt',
        ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_compress_dir(tmp_empty):
    dir = Path('dist', 'project-name')
    dir.mkdir(parents=True)

    (dir / 'file').touch()

    source.compress_dir('dist/project-name', 'dist/project-name.tar.gz')

    with tarfile.open('dist/project-name.tar.gz', 'r:gz') as tar:
        tar.extractall('.')

    expected = set(Path(p) for p in (
        'project-name',
        'project-name/file',
    ))
    assert set(Path(p) for p in source.glob_all('project-name')) == expected
