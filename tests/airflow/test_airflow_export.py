import shutil
import os
import subprocess
import importlib
from unittest.mock import Mock, ANY
from pathlib import Path
import json

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod \
    import KubernetesPodOperator
import pytest

from conftest import _mock_docker_calls
from soopervisor.airflow.export import AirflowExporter, commons
from soopervisor.exceptions import ConfigurationError


def git_init():
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


@pytest.fixture
def mock_docker_calls(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_docker_calls(monkeypatch, cmd, 'sample_project', 'latest')


@pytest.fixture
def mock_docker_calls_serve(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.serve.yaml").to_dag().clients)')
    yield _mock_docker_calls(monkeypatch, cmd, 'sample_project', 'latest')


@pytest.fixture
def mock_docker_calls_callables(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_docker_calls(monkeypatch, cmd, 'callables', 'latest')


# need to modify the env.airflow.yaml name
# better to move to project's CI
@pytest.mark.skip
@pytest.mark.parametrize(
    'name',
    [
        'ml-intermediate',
        'etl',
        'ml-online',
    ],
)
def test_generate_valid_airflow_dags(name, tmp_projects):
    # TODO: clean up projects/ source code and remove the soopervisor.yaml,
    # they should
    # work without one

    if name == 'ml-online':
        subprocess.run(['pip', 'uninstall', 'ml-online', '--yes'], check=True)
        subprocess.run(['pip', 'install', 'ml-online/'], check=True)

    os.chdir(name)

    subprocess.run([
        'soopervisor',
        'add',
        'serve',
        '--backend',
        'airflow',
    ],
                   check=True)

    subprocess.run(['python', f'serve/dags/{name}.py'], check=True)


def test_airflow_add_sample_project(monkeypatch, tmp_sample_project,
                                    no_sys_modules_cache):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')
    exporter.add()

    assert set(os.listdir('serve')) == {'sample_project.py', 'Dockerfile'}


def test_airflow_export_sample_project(monkeypatch, mock_docker_calls,
                                       tmp_sample_project,
                                       no_sys_modules_cache,
                                       skip_repo_validation):
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    # this requires a git repo
    git_init()

    exporter.add()
    exporter.export(mode='incremental')

    monkeypatch.syspath_prepend('serve')
    mod = importlib.import_module('sample_project')
    dag = mod.dag

    load_tasks_mock.assert_called_once_with(cmdr=ANY,
                                            name='serve',
                                            mode='incremental')
    assert isinstance(dag, DAG)
    assert set(dag.task_dict) == {'clean', 'plot', 'raw'}
    assert set(type(t) for t in dag.tasks) == {KubernetesPodOperator}
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'raw': set(),
                'clean': {'raw'},
                'plot': {'clean'}
            }

    spec = json.loads(Path('serve', 'sample_project.json').read_text())

    assert [t['command'] for t in spec['tasks']] == [
        'ploomber task raw --entry-point pipeline.yaml',
        'ploomber task clean --entry-point pipeline.yaml',
        'ploomber task plot --entry-point pipeline.yaml'
    ]


@pytest.mark.parametrize('mode, args', [
    ['incremental', ''],
    ['regular', ''],
    ['force', ' --force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_export_airflow_callables(monkeypatch, mock_docker_calls_callables,
                                  tmp_callables, no_sys_modules_cache,
                                  skip_repo_validation, mode, args):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    # this requires a git repo
    git_init()

    exporter.add()
    exporter.export(mode=mode)

    monkeypatch.syspath_prepend(Path('serve').resolve())

    mod = importlib.import_module('callables')
    dag = mod.dag

    assert isinstance(dag, DAG)
    # check tasks in dag
    assert set(dag.task_dict) == {'features', 'fit', 'get', 'join'}
    # check task's class
    assert set(type(t) for t in dag.tasks) == {KubernetesPodOperator}
    # check dependencies
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'get': set(),
                'features': {'get'},
                'join': {'features', 'get'},
                'fit': {'join'}
            }

    # check generated scripts
    td = dag.task_dict
    template = 'ploomber task {} --entry-point pipeline.yaml'
    assert td['get'].arguments == [template.format('get') + args]
    assert td['features'].arguments == [template.format('features') + args]
    assert td['fit'].arguments == [template.format('fit') + args]
    assert td['join'].arguments == [template.format('join') + args]

    assert {t.image for t in td.values()} == {'image_target:latest'}
    assert {tuple(t.cmds) for t in td.values()} == {('bash', '-cx')}


def test_stops_if_no_tasks(monkeypatch, mock_docker_calls, tmp_sample_project,
                           no_sys_modules_cache, capsys):
    load_tasks_mock = Mock(return_value=([], []))
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    git_init()

    exporter.add()
    exporter.export(mode='incremental')

    captured = capsys.readouterr()
    assert 'has no tasks to submit.' in captured.out


def test_validates_repository(monkeypatch, mock_docker_calls,
                              tmp_sample_project, no_sys_modules_cache):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    exporter.add()

    with pytest.raises(ConfigurationError) as excinfo:
        exporter.export(mode='incremental')

    assert str(
        excinfo.value) == ("Invalid repository 'your-repository/name' "
                           "in soopervisor.yaml, please add a valid value.")


def test_skip_tests(monkeypatch, mock_docker_calls, tmp_sample_project,
                    no_sys_modules_cache, skip_repo_validation, capsys):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    git_init()

    exporter.add()
    exporter.export(mode='incremental', skip_tests=True)

    captured = capsys.readouterr()
    assert 'Testing image' not in captured.out
    assert 'Testing File client' not in captured.out


# TODO: check with packaged project
def test_checks_the_right_spec(monkeypatch, mock_docker_calls_serve,
                               tmp_sample_project, no_sys_modules_cache,
                               skip_repo_validation):
    shutil.copy('pipeline.yaml', 'pipeline.serve.yaml')

    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    exporter.add()
    exporter.export(mode='incremental')

    expected = ('docker', 'run', 'sample_project:latest', 'ploomber', 'status',
                '--entry-point', 'pipeline.serve.yaml')
    assert mock_docker_calls_serve.calls[1] == expected


def test_dockerfile_when_no_setup_py(tmp_sample_project, no_sys_modules_cache):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    exporter.add()

    dockerfile = Path('serve', 'Dockerfile').read_text()
    assert 'RUN pip install *.tar.gz --no-deps' not in dockerfile
