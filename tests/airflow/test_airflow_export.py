import os
import subprocess
import importlib
from unittest.mock import Mock, ANY
from pathlib import Path
import json

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod \
    import KubernetesPodOperator
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator
import pytest

from conftest import _mock_commander_calls, git_init
from soopervisor.airflow.export import AirflowExporter, commons


@pytest.fixture
def mock_docker_calls_callables(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_commander_calls(monkeypatch, cmd, 'callables', 'latest')


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


@pytest.mark.parametrize('preset, operator_class, needs_docker', [
    [None, KubernetesPodOperator, True],
    ['kubernetes', KubernetesPodOperator, True],
    ['bash', BashOperator, False],
    ['docker', DockerOperator, True],
],
                         ids=[
                             'none',
                             'kubernetes',
                             'bash',
                             'docker',
                         ])
def test_airflow_export_sample_project(
    monkeypatch,
    mock_docker_sample_project,
    tmp_sample_project,
    no_sys_modules_cache,
    skip_repo_validation,
    preset,
    operator_class,
    needs_docker,
):
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = AirflowExporter.new(path_to_config='soopervisor.yaml',
                                   env_name='serve',
                                   preset=preset)

    # this requires a git repo
    git_init()

    exporter.add()

    exporter.export(mode='incremental')

    # if we do no call .resolve(), .import_module will keep loading the module
    # from the previous parametrization (idk why)
    monkeypatch.syspath_prepend(Path('serve').resolve())

    mod = importlib.import_module('sample_project')
    dag = mod.dag

    load_tasks_mock.assert_called_once_with(cmdr=ANY,
                                            name='serve',
                                            mode='incremental')
    assert isinstance(dag, DAG)
    assert set(dag.task_dict) == {'clean', 'plot', 'raw'}
    assert set(type(t) for t in dag.tasks) == {operator_class}
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

    # Dockerfile should only exist if needed
    assert ((Path('serve', 'Dockerfile').exists() and needs_docker)
            or (not Path('serve', 'Dockerfile').exists() and not needs_docker))


@pytest.mark.parametrize('mode, args', [
    ['incremental', ''],
    ['regular', ''],
    ['force', ' --force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_export_airflow_callables(monkeypatch, mock_docker_calls_callables,
                                  tmp_callables, no_sys_modules_cache,
                                  skip_repo_validation, mode, args):
    exporter = AirflowExporter.new(path_to_config='soopervisor.yaml',
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

    assert {t.image for t in td.values()} == {'your-repository/name:latest'}
    assert {tuple(t.cmds) for t in td.values()} == {('bash', '-cx')}
