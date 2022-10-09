import os
import tarfile
import subprocess
from pathlib import Path
from unittest.mock import Mock

import yaml
import pytest
from click import ClickException
from ploomber.spec import DAGSpec
from ploomber.executors import Serial
from ploomber.io._commander import Commander

from soopervisor.commons import source, conda, dependencies
from soopervisor import commons
from soopervisor.exceptions import MissingDockerfileError
from soopervisor.abc import AbstractDockerConfig

from conftest import CustomCommander


class ConcreteDockerConfig(AbstractDockerConfig):

    @classmethod
    def get_backend_value(self):
        return 'backend-value'


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
    subprocess.check_call(['git', 'config', 'commit.gpgsign', 'false'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


def git_commit():
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


def test_copy_with_rename(cmdr, tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'another').touch()
    rename_files = {'file': 'file_another'}
    git_init()

    source.copy(cmdr, '.', 'dist', rename_files=rename_files)

    expected = set(
        Path(p) for p in (
            'dist/file_another',
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


def test_git_tracked_files(tmp_empty):
    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'another').touch()
    git_init()

    assert {'dir/another', 'file'} == set(source.git_tracked_files()[0])


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

    assert 'Your git repository contains uncommitted' in captured.out


def test_errors_if_no_tracked_files(tmp_empty):

    Path('file').touch()
    git_init()

    dir_ = Path('dir')
    dir_.mkdir()
    os.chdir(dir_)

    Path('another').touch()

    with pytest.raises(ClickException) as excinfo:
        with Commander() as cmdr:
            source.copy(cmdr, '.', 'dist')

    expected = ('Running inside a git repository, but no files in '
                'the current working directory are tracked by git. Commit the '
                'files to include them in the Docker image or pass the '
                '--ignore-git flag to soopervisor export')
    assert str(excinfo.value) == expected


def test_copy_ignore_git(tmp_empty):
    Path('file').touch()
    git_init()

    dir_ = Path('dir')
    dir_.mkdir()
    os.chdir(dir_)

    Path('another').touch()

    with Commander() as cmdr:
        source.copy(cmdr, '.', 'dist', ignore_git=True)

    assert Path('dist', 'another').is_file()


def test_copy_warn_if_file_too_big(cmdr, tmp_empty, monkeypatch, capsys):
    # mock files to be 11MB
    monkeypatch.setattr(source.os.path, 'getsize',
                        Mock(return_value=1024 * 1024 * 11.1243214124))

    Path('file').touch()
    Path('dir').mkdir()
    Path('dir', 'another').touch()
    Path('dir', 'others').touch()
    git_init()

    source.copy(cmdr, '.', 'dist')

    expected = set(
        Path(p) for p in (
            'dist/file',
            'dist/dir/another',
            'dist/dir/others',
        ))

    captured = capsys.readouterr()

    assert set(Path(p) for p in source.glob_all('dist')) == expected
    assert 'The following files are too big. ' in captured.out
    assert 'file' in captured.out


def test_compress_dir(tmp_empty):
    dir = Path('dist', 'project-name')
    dir.mkdir(parents=True)
    (dir / 'file').touch()

    with Commander() as cmdr:
        source.compress_dir(cmdr, 'dist/project-name',
                            'dist/project-name.tar.gz')

    with tarfile.open('dist/project-name.tar.gz', 'r:gz') as tar:
        tar.extractall('.')

    expected = {Path('project-name/file')}
    assert set(Path(p) for p in source.glob_all('project-name')) == expected


def test_compress_warns_if_output_too_big(tmp_empty, monkeypatch, capsys):
    # mock a file of 6MB
    monkeypatch.setattr(source.os.path, 'getsize',
                        Mock(return_value=1024 * 1024 * 6))

    dir = Path('dist', 'project-name')
    dir.mkdir(parents=True)
    (dir / 'file').touch()

    with Commander() as cmdr:
        source.compress_dir(cmdr, 'dist/project-name',
                            'dist/project-name.tar.gz')

    captured = capsys.readouterr()
    expected = ("The project's source code 'dist/project-name.tar.gz' "
                "is larger than 5MB")
    assert expected in captured.out


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
    ['incremental', {}, ['--entry-point', 'pipeline.yaml']],
    [
        'regular', {
            'root': [],
            'another': ['root']
        }, ['--entry-point', 'pipeline.yaml']
    ],
    [
        'force', {
            'root': [],
            'another': ['root']
        }, ['--entry-point', 'pipeline.yaml', '--force']
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
    }, ['--entry-point', 'pipeline.yaml']],
    [
        'regular', {
            'root': [],
            'another': ['root']
        }, ['--entry-point', 'pipeline.yaml']
    ],
    [
        'force', {
            'root': [],
            'another': ['root']
        }, ['--entry-point', 'pipeline.yaml', '--force']
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

    assert "'mode' must be one of" in str(excinfo.value)


def test_loads_pipeline_with_name(cmdr, tmp_fast_pipeline):
    os.rename('pipeline.yaml', 'pipeline.train.yaml')

    # we need this to set our project root
    Path('pipeline.yaml').touch()

    _, args = commons.load_tasks(cmdr, name='train')
    assert args == ['--entry-point', 'pipeline.train.yaml']


def test_loads_pipeline_in_package_with_name(cmdr, backup_packaged_project):
    os.rename(Path('src', 'my_project', 'pipeline.yaml'),
              Path('src', 'my_project', 'pipeline.train.yaml'))
    _, args = commons.load_tasks(cmdr, name='train')

    assert args == [
        '--entry-point',
        str(Path('src/my_project/pipeline.train.yaml'))
    ]


def test_check_lock_files_exist(tmp_empty):

    with pytest.raises(ClickException) as excinfo:
        dependencies.check_lock_files_exist()

    expected = ('Expected requirements.lock.txt or environment.lock.yml at '
                'the root directory')
    assert expected in str(excinfo.value)


def test_check_lock_files_exist_multiple_dependency(tmp_empty):

    Path('requirements.txt').touch()
    Path('requirements.lock.txt').touch()
    Path('requirements.fit-__.txt').touch()

    with pytest.raises(ClickException) as excinfo:
        dependencies.check_lock_files_exist()

    expected = ('Expected requirements.<task-name>.lock.txt file for \
        each requirements.<task-name>.txt file ')
    assert expected in str(excinfo.value)


def test_error_if_missing_dockerfile(tmp_empty):
    with pytest.raises(MissingDockerfileError) as excinfo:
        commons.docker.build(e=Mock(),
                             cfg=Mock(),
                             env_name='some_name',
                             until=Mock(),
                             entry_point=Mock())

    assert excinfo.value.env_name == 'some_name'


def _list_files(path):
    """Return files in a .tar.gz file, ignoring hidden files
    """
    with tarfile.open(path) as tar:
        return set(f for f in tar.getnames()
                   if not Path(f).name.startswith('.'))


@pytest.mark.xfail(reason='current implementation overwrites files')
def test_cp_ploomber_home(tmp_empty, monkeypatch):
    monkeypatch.setattr(commons.docker.telemetry, 'get_home_dir', lambda: '.')

    Path('stats').mkdir()
    Path('stats', 'another').touch()
    Path('dist').mkdir()
    Path('file').touch()
    path = Path('dist', 'some-package.tar.gz')

    with tarfile.open(path, 'w:gz') as tar:
        tar.add('file')

    before = _list_files(path)
    commons.docker.cp_ploomber_home('some-package')
    after = _list_files(path)

    assert before == {'file'}
    assert after == {'ploomber/stats', 'ploomber/stats/another', 'file'}


def test_get_dependencies(tmp_empty):
    Path('requirements.txt').touch()
    Path('requirements.lock.txt').touch()
    Path('requirements.clean-__.txt').touch()
    Path('requirements.clean-__.lock.txt').touch()
    Path('requirements.load-__.txt').touch()
    Path('requirements.load-__.lock.txt').touch()

    dependency_files, lock_paths = commons.docker.get_dependencies()

    expected_dependency_files = {
        'load-*': {
            'dependency': 'requirements.load-__.txt',
            'lock': 'requirements.load-__.lock.txt'
        },
        'default': {
            'dependency': 'requirements.txt',
            'lock': 'requirements.lock.txt'
        },
        'clean-*': {
            'lock': 'requirements.clean-__.lock.txt',
            'dependency': 'requirements.clean-__.txt'
        }
    }
    expected_lock_paths = {
        'load-*': 'requirements.load-__.lock.txt',
        'default': 'requirements.lock.txt',
        'clean-*': 'requirements.clean-__.lock.txt'
    }
    assert dependency_files == expected_dependency_files
    assert lock_paths == expected_lock_paths


def test_docker_build(tmp_sample_project):
    Path('some-env').mkdir()
    Path('some-env', 'Dockerfile').touch()

    with CustomCommander(workspace='some-env') as cmdr:
        commons.docker.build(cmdr,
                             ConcreteDockerConfig(),
                             'some-env',
                             until=None,
                             entry_point='pipeline.yaml')

    existing = _list_files(Path('dist', 'sample_project.tar.gz'))

    expected = {
        'sample_project/env.serve.yaml',
        'sample_project',
        'sample_project/some-env/Dockerfile',
        'sample_project/clean.py',
        'sample_project/plot.py',
        'sample_project/environment.yml',
        'sample_project/env.yaml',
        'sample_project/README.md',
        'sample_project/environment.lock.yml',
        'sample_project/some-env',
        'sample_project/some-env/environment.lock.yml',
        'sample_project/raw.py',
        'sample_project/pipeline.yaml',
        'sample_project/lib/__init__.py',
        'sample_project/lib',
        'sample_project/lib/package_a.py',
    }

    assert existing == expected

    # check tag name
    cmd = cmdr.docker_cmds[0][0]
    name, tag = cmd[1], cmd[-1]
    assert name == 'build' and tag == 'sample_project:latest'


@pytest.mark.parametrize('repo, expected', [
    ['docker.company.com/something', 'docker.company.com/something:latest'],
    ['docker.company.com/something:v2', 'docker.company.com/something:v2'],
])
def test_docker_build_with_repository(tmp_sample_project, repo, expected):
    Path('some-env').mkdir()
    Path('some-env', 'Dockerfile').touch()

    cfg = ConcreteDockerConfig(repository=repo)

    with CustomCommander(workspace='some-env') as cmdr:
        commons.docker.build(cmdr,
                             cfg,
                             'some-env',
                             until=None,
                             entry_point='pipeline.yaml')
    # check tag name
    cmd = cmdr.docker_cmds[0][0]
    assert cmd == (
        'docker',
        'build',
        '.',
        '--tag',
        'sample_project:latest',
    )

    # check tag command
    cmd = cmdr.docker_cmds[-2][0]
    assert cmd == (
        'docker',
        'tag',
        'sample_project:latest',
        expected,
    )


def test_docker_build_multiple_requirement(
        tmp_sample_project_multiple_requirement):
    Path('some-env').mkdir()
    Path('some-env', 'Dockerfile').touch()

    with CustomCommander(workspace='some-env') as cmdr:
        pkg_name, image_map = \
            commons.docker.build(cmdr,
                                 ConcreteDockerConfig(),
                                 'some-env',
                                 until=None,
                                 entry_point='pipeline.yaml')

    # validate docker is called with the right arguments
    docker_args = [args[0] for args in cmdr.docker_cmds]

    def generate_commands(suffix):
        image_name = f'multiple_requirements_project{suffix}:latest'

        return [
            # build image
            (
                'docker',
                'build',
                '.',
                '--tag',
                image_name,
            ),
            # check pipeline load
            (
                'docker',
                'run',
                image_name,
                'ploomber',
                'status',
                '--entry-point',
                'pipeline.yaml',
            ),
            # check pipeline has a client
            (
                'docker',
                'run',
                image_name,
                'python',
                '-c',
                ('from ploomber.spec import DAGSpec; '
                 'print("File" in DAGSpec("pipeline.yaml").to_dag().clients)'),
            )
        ]

    assert generate_commands('-clean-ploomber') == docker_args[:3]
    assert generate_commands('') == docker_args[3:6]
    assert generate_commands('-plot-ploomber') == docker_args[6:]

    assert pkg_name == 'multiple_requirements_project'
    assert image_map == \
           {'default': 'multiple_requirements_project:latest',
            'clean-*': 'multiple_requirements_project-clean-ploomber:latest',
            'plot-*': 'multiple_requirements_project-plot-ploomber:latest'}

    existing = _list_files(Path('dist',
                                'multiple_requirements_project.tar.gz'))

    expected = {
        'multiple_requirements_project/env.serve.yaml',
        'multiple_requirements_project',
        'multiple_requirements_project/some-env/Dockerfile',
        'multiple_requirements_project/clean_one.py',
        'multiple_requirements_project/clean_two.py',
        'multiple_requirements_project/plot.py',
        'multiple_requirements_project/env.yaml',
        'multiple_requirements_project/README.md',
        'multiple_requirements_project/some-env',
        'multiple_requirements_project/raw.py',
        'multiple_requirements_project/pipeline.yaml',
        'multiple_requirements_project/requirements.txt',
        'multiple_requirements_project/requirements.lock.txt',
        'multiple_requirements_project/requirements.clean-__.txt',
        'multiple_requirements_project/requirements.plot-__.txt',
        'multiple_requirements_project/some-env/requirements.lock.txt',
        'multiple_requirements_project/some-env/requirements.clean-__.'
        'lock.txt',
        'multiple_requirements_project/some-env/requirements.plot-__.lock.txt'
    }

    assert existing == expected


def test_docker_build_multiple_requirement_with_setup(
        tmp_sample_project_multiple_requirement):
    Path('some-env').mkdir()
    Path('some-env', 'Dockerfile').touch()
    Path('setup.py').touch()

    with pytest.raises(NotImplementedError) as excinfo:
        commons.docker.build(CustomCommander(workspace='some-env'),
                             ConcreteDockerConfig(),
                             'some-env',
                             until=None,
                             entry_point='pipeline.yaml')

    expected = ('Multiple requirements.*.lock.txt or environment.*.lock.yml '
                'files found along with setup.py file.')
    assert expected in str(excinfo.value)


def test_docker_build_big_file_warns(tmp_sample_project, monkeypatch, capsys):
    monkeypatch.setattr(source.os.path, 'getsize',
                        Mock(return_value=1024 * 1024 * 11))

    Path('some-env').mkdir()
    Path('some-env', 'Dockerfile').touch()

    with CustomCommander(workspace='some-env') as cmdr:
        commons.docker.build(cmdr,
                             ConcreteDockerConfig(),
                             'some-env',
                             until=None,
                             entry_point='pipeline.yaml')

    existing = _list_files(Path('dist', 'sample_project.tar.gz'))

    expected = {
        'sample_project/env.serve.yaml',
        'sample_project',
        'sample_project/some-env/Dockerfile',
        'sample_project/clean.py',
        'sample_project/plot.py',
        'sample_project/environment.yml',
        'sample_project/env.yaml',
        'sample_project/README.md',
        'sample_project/environment.lock.yml',
        'sample_project/some-env',
        'sample_project/some-env/environment.lock.yml',
        'sample_project/raw.py',
        'sample_project/pipeline.yaml',
        'sample_project/lib/__init__.py',
        'sample_project/lib',
        'sample_project/lib/package_a.py',
    }

    captured = capsys.readouterr()

    assert existing == expected

    assert 'The following files are too big. ' in captured.out
    assert 'README.md' in captured.out
    assert 'raw.py' in captured.out


def test_lazily_load_dag(tmp_empty):
    Path('script.py').write_text("""
import some_unknown_package

# %% + tags = ["parameters"]
upstream = None

# %%
1 + 1
""")

    Path('tasks.py').write_text("""
import another_unknown_package

def some_task(product):
    pass
""")

    Path('clients.py').write_text("""
from ploomber.clients import LocalStorageClient

def get_client():
    return LocalStorageClient(path_to_backup_dir='backup')
""")

    spec = {
        'tasks': [
            {
                'source': 'script.py',
                'product': 'report.html'
            },
            {
                'source': 'tasks.some_task',
                'product': 'out.csv'
            },
        ],
        'clients': {
            'File': 'clients.get_client'
        }
    }

    Path('pipeline.yaml').write_text(yaml.safe_dump(spec))

    commons.load_dag(cmdr=Mock(), name='name', lazy_import=True)
