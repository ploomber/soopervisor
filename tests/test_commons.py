import os
import tarfile
import subprocess
from pathlib import Path

import yaml
import pytest
from click import ClickException
from ploomber.spec import DAGSpec
from ploomber.executors import Serial
from ploomber.io._commander import Commander

from soopervisor.commons import source, conda, dependencies
from soopervisor import commons


@pytest.fixture
def cmdr():
    with Commander() as cmdr:
        yield cmdr


def git_init():
    # to prevent overwriting the repo's settings
    if 'soopervisor' in str(Path('.').resolve()):
        raise ValueError('This doesnt look like a tmp directory. '
                         'Did you forget the tmp_empty fixture?')

    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


def test_glob_all_excludes_directories(tmp_empty):
    Path('dir').mkdir()
    Path('dir', 'a').touch()

    assert set(Path(p) for p in source.glob_all('.')) == {Path('dir', 'a')}


def test_global_all_excludes_from_arg(tmp_empty):
    Path('dir').mkdir()
    Path('dir', 'a').touch()
    Path('excluded').mkdir()
    Path('excluded', 'should-not-appear').touch()

    assert set(Path(p) for p in source.glob_all('.', exclude='excluded')) == {
        Path('dir', 'a')
    }


def test_copy(cmdr, tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'another').touch()
    git_init()
    source.copy(cmdr, '.', 'dist')

    expected = set(Path(p) for p in (
        'dist/file',
        'dist/dir/another',
    ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_copy_with_gitignore(cmdr, tmp_empty):
    Path('file').touch()
    Path('ignoreme').touch()

    Path('.gitignore').write_text('ignoreme')
    git_init()
    source.copy(cmdr, '.', 'dist')

    expected = set({Path('dist/file')})
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_error_if_exclude_and_include_overlap(cmdr, tmp_empty):

    with pytest.raises(ClickException) as excinfo:
        source.copy(cmdr, '.', 'dist', exclude=['file'], include=['file'])

    expected = ("include and exclude must "
                "not have overlapping elements: {'file'}")
    assert expected == str(excinfo.value)


def test_override_git_with_exclude(cmdr, tmp_empty):
    Path('file').touch()
    Path('secrets.txt').touch()

    # let git track everything
    Path('.gitignore').touch()
    git_init()

    # exclude some file
    source.copy(cmdr, '.', 'dist', exclude=['file'])

    expected = set({Path('dist/secrets.txt')})
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_copy_override_gitignore_with_include(cmdr, tmp_empty):
    Path('file').touch()
    Path('secrets.txt').touch()

    Path('.gitignore').write_text('secrets.txt')
    git_init()

    source.copy(cmdr, '.', 'dist', include=['secrets.txt'])

    expected = set(Path(p) for p in (
        'dist/file',
        'dist/secrets.txt',
    ))

    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_copy_override_gitignore_with_include_entire_folder(cmdr, tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'secrets.txt').touch()
    Path('dir', 'more-secrets.txt').touch()

    Path('.gitignore').write_text('dir')
    git_init()

    source.copy(cmdr, '.', 'dist', include=['dir'])

    expected = set(
        Path(p) for p in (
            'dist/file',
            'dist/dir/secrets.txt',
            'dist/dir/more-secrets.txt',
        ))

    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_no_git_but_exclude(cmdr, tmp_empty):
    Path('file').touch()
    Path('secrets.txt').touch()

    source.copy(cmdr, '.', 'dist', exclude=['secrets.txt'])

    expected = set(Path(p) for p in ('dist/file', ))

    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_no_git_but_exclude_entire_folder(cmdr, tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'secrets.txt').touch()
    Path('dir', 'more-secrets.txt').touch()

    source.copy(cmdr, '.', 'dist', exclude=['dir'])

    expected = set(Path(p) for p in ('dist/file', ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_ignores_pycache(cmdr, tmp_empty):
    Path('file').touch()
    dir_ = Path('__pycache__')
    dir_.mkdir()
    (dir_ / 'file').touch()
    (dir_ / 'another').touch()
    dir_another = Path('subdir', '__pycache__')
    dir_another.mkdir(parents=True)
    (dir_another / 'file').touch()
    (dir_another / 'another').touch()

    source.copy(cmdr, '.', 'dist')

    expected = set(Path(p) for p in ('dist/file', ))
    assert set(Path(p) for p in source.glob_all('dist')) == expected


def test_warns_if_fails_to_get_git_tracked_files(tmp_empty, capsys):
    Path('file').touch()
    Path('secrets.txt').touch()

    with Commander() as cmdr:
        source.copy(cmdr, '.', 'dist')

    captured = capsys.readouterr()

    assert 'Unable to get git tracked files' in captured.out


def test_warns_on_dirty_git(tmp_empty, capsys):
    Path('file').touch()
    Path('secrets.txt').touch()

    Path('.gitignore').write_text('secrets.txt')
    git_init()

    Path('new-file').touch()

    with Commander() as cmdr:
        source.copy(cmdr, '.', 'dist')

    captured = capsys.readouterr()

    assert 'Your git repository contains untracked' in captured.out


def test_compress_dir(tmp_empty):
    dir = Path('dist', 'project-name')
    dir.mkdir(parents=True)

    (dir / 'file').touch()

    source.compress_dir('dist/project-name', 'dist/project-name.tar.gz')

    with tarfile.open('dist/project-name.tar.gz', 'r:gz') as tar:
        tar.extractall('.')

    expected = {Path('project-name/file')}
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
    ['incremental', {}, ['--entry-point pipeline.yaml']],
    [
        'regular', {
            'root': [],
            'another': ['root']
        }, ['--entry-point pipeline.yaml']
    ],
    [
        'force', {
            'root': [],
            'another': ['root']
        }, ['--entry-point pipeline.yaml', '--force']
    ],
])
def test_load_tasks(cmdr, tmp_fast_pipeline, add_current_to_sys_path,
                    dag_build, mode, tasks_expected, args_expected):
    tasks, args = commons.load_tasks(cmdr=cmdr, mode=mode)
    assert tasks == tasks_expected
    assert args == args_expected


@pytest.mark.parametrize('mode, tasks_expected, args_expected', [
    ['incremental', {
        'another': []
    }, ['--entry-point pipeline.yaml']],
    [
        'regular', {
            'root': [],
            'another': ['root']
        }, ['--entry-point pipeline.yaml']
    ],
    [
        'force', {
            'root': [],
            'another': ['root']
        }, ['--entry-point pipeline.yaml', '--force']
    ],
])
def test_load_tasks_missing_remote_metadata(cmdr, tmp_fast_pipeline,
                                            add_current_to_sys_path, dag_build,
                                            mode, tasks_expected,
                                            args_expected):
    Path('remote', 'out', 'another').unlink()
    tasks, args = commons.load_tasks(cmdr=cmdr, mode=mode)
    assert tasks == tasks_expected
    assert args == args_expected


def test_invalid_mode(cmdr, tmp_fast_pipeline):
    with pytest.raises(ValueError) as excinfo:
        commons.load_tasks(cmdr=cmdr, mode='unknown')

    assert 'mode must be one of' in str(excinfo.value)


def test_loads_pipeline_with_name(cmdr, tmp_fast_pipeline):
    os.rename('pipeline.yaml', 'pipeline.train.yaml')

    # we need this to set our project root
    Path('pipeline.yaml').touch()

    _, args = commons.load_tasks(cmdr, name='train')
    assert args == ['--entry-point pipeline.train.yaml']


def test_loads_pipeline_in_package_with_name(cmdr, backup_packaged_project):
    os.rename(Path('src', 'my_project', 'pipeline.yaml'),
              Path('src', 'my_project', 'pipeline.train.yaml'))
    _, args = commons.load_tasks(cmdr, name='train')

    assert args == ['--entry-point src/my_project/pipeline.train.yaml']


def test_check_lock_files_exist(tmp_empty):

    with pytest.raises(ClickException) as excinfo:
        dependencies.check_lock_files_exist()

    expected = ('Expected requirements.txt.lock or environment.lock.yml at '
                'the root directory')
    assert expected in str(excinfo.value)
