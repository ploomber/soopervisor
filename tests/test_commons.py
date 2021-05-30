import tarfile
import subprocess
from pathlib import Path

import yaml
import pytest
from click import ClickException
from ploomber.spec import DAGSpec
from ploomber.executors import Serial

from soopervisor.commons import source, conda
from soopervisor import commons


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


@pytest.mark.parametrize('env_yaml, expected', [
    [{
        'dependencies': ['a', 'b', {
            'pip': ['c', 'd']
        }]
    }, ['c', 'd']],
    [{
        'dependencies': [{
            'pip': ['y', 'z']
        }, 'a', 'b']
    }, ['y', 'z']],
])
def test_extract_pip_from_env_yaml(tmp_empty, env_yaml, expected):
    Path('environment.yml').write_text(yaml.safe_dump(env_yaml))
    assert conda.extract_pip_from_env_yaml('environment.yml') == expected


def test_error_extract_pip_missing_dependencies_section():
    Path('environment.yml').write_text(yaml.safe_dump({}))

    with pytest.raises(ClickException) as excinfo:
        conda.extract_pip_from_env_yaml('environment.yml')

    msg = ('Cannot extract pip dependencies from environment.lock.yml: '
           'missing dependencies section')
    assert msg == str(excinfo.value)


def test_error_extract_pip_missing_pip_dict():
    Path('environment.yml').write_text(
        yaml.safe_dump({'dependencies': ['a', 'b']}))

    with pytest.raises(ClickException) as excinfo:
        conda.extract_pip_from_env_yaml('environment.yml')

    msg = ('Cannot extract pip dependencies from environment.lock.yml: '
           'missing dependencies.pip section')
    assert msg == str(excinfo.value)


def test_error_extract_pip_unexpected_pip_list():
    Path('environment.yml').write_text(
        yaml.safe_dump({'dependencies': ['a', 'b', {
            'pip': 1
        }]}))

    with pytest.raises(ClickException) as excinfo:
        conda.extract_pip_from_env_yaml('environment.yml')

    msg = ('Cannot extract pip dependencies from environment.lock.yml: '
           'unexpected dependencies.pip value. Expected a list of '
           'dependencies, got: 1')
    assert msg == str(excinfo.value)


@pytest.fixture
def dag_build():
    dag = DAGSpec.find().to_dag()
    dag.executor = Serial(build_in_subprocess=False)
    dag.render().build()


@pytest.mark.parametrize('mode, tasks_expected, args_expected', [
    ['incremental', {}, []],
    ['regular', {
        'root': [],
        'another': ['root']
    }, []],
    ['force', {
        'root': [],
        'another': ['root']
    }, ['--force']],
])
def test_load_tasks(tmp_fast_pipeline, add_current_to_sys_path, dag_build,
                    mode, tasks_expected, args_expected):
    tasks, args = commons.load_tasks(mode=mode)
    assert tasks == tasks_expected
    assert args == args_expected


@pytest.mark.parametrize('mode, tasks_expected, args_expected', [
    ['incremental', {
        'another': []
    }, []],
    ['regular', {
        'root': [],
        'another': ['root']
    }, []],
    ['force', {
        'root': [],
        'another': ['root']
    }, ['--force']],
])
def test_load_tasks_missing_remote_metadata(tmp_fast_pipeline,
                                            add_current_to_sys_path, dag_build,
                                            mode, tasks_expected,
                                            args_expected):
    Path('remote', 'out', 'another').unlink()
    tasks, args = commons.load_tasks(mode=mode)
    assert tasks == tasks_expected
    assert args == args_expected


def test_invalid_mode():
    with pytest.raises(ValueError) as excinfo:
        commons.load_tasks(mode='unknown')

    assert 'mode must be one of' in str(excinfo.value)
