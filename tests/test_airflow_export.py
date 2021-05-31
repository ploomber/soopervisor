import os
import subprocess
import importlib
from unittest.mock import Mock

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from ploomber.io import _commander, _commander_tester
import pytest

from soopervisor.airflow.export import AirflowExporter, commons


def git_init():
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


@pytest.fixture
def mock_docker_calls(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in DAGSpec.find().to_dag().clients)')
    tester = _commander_tester.CommanderTester(return_value={
        ('docker', 'run', 'sample_project:latest', 'python', '-c', cmd):
        b'True\n'
    })

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)


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
                                       no_sys_modules_cache):
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

    load_tasks_mock.assert_called_once_with(mode='incremental')
    assert isinstance(dag, DAG)
    assert set(dag.task_dict) == {'clean', 'plot', 'raw'}
    assert set(type(t) for t in dag.tasks) == {DockerOperator}
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'raw': set(),
                'clean': {'raw'},
                'plot': {'clean'}
            }


@pytest.fixture
def mock_docker_calls_callables(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in DAGSpec.find().to_dag().clients)')
    tester = _commander_tester.CommanderTester(return_value={
        ('docker', 'run', 'callables:latest', 'python', '-c', cmd):
        b'True\n'
    })

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)


@pytest.mark.parametrize('mode, args', [
    ['incremental', ''],
    ['regular', ''],
    ['force', ' --force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_export_airflow_callables(monkeypatch, mock_docker_calls_callables,
                                  tmp_callables, no_sys_modules_cache, mode,
                                  args):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    # this requires a git repo
    git_init()

    exporter.add()
    exporter.export(mode=mode)

    monkeypatch.syspath_prepend('serve')
    mod = importlib.import_module('callables')
    dag = mod.dag

    assert isinstance(dag, DAG)
    # check tasks in dag
    assert set(dag.task_dict) == {'features', 'fit', 'get', 'join'}
    # check task's class
    assert set(type(t) for t in dag.tasks) == {DockerOperator}
    # check dependencies
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'get': set(),
                'features': {'get'},
                'join': {'features', 'get'},
                'fit': {'join'}
            }

    # check generated scripts
    assert dag.task_dict['get'].command == 'ploomber task get' + args
    assert dag.task_dict['features'].command == 'ploomber task features' + args
    assert dag.task_dict['fit'].command == 'ploomber task fit' + args
    assert dag.task_dict['join'].command == 'ploomber task join' + args


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


def test_skip_tests(monkeypatch, mock_docker_calls, tmp_sample_project,
                    no_sys_modules_cache, capsys):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')

    git_init()

    exporter.add()
    exporter.export(mode='incremental', skip_tests=True)

    captured = capsys.readouterr()
    assert 'Testing image' not in captured.out
    assert 'Testing File client' not in captured.out
