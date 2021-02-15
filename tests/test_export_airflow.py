import subprocess
from pathlib import Path
import importlib

from airflow import DAG
from airflow.operators.bash import BashOperator
import pytest

from soopervisor.airflow import export
from soopervisor.base.config import ScriptConfig


@pytest.mark.parametrize(
    'name',
    ['ml-intermediate', 'etl', 'ml-online'],
)
def test_generate_valid_airflow_dags(name, tmp_projects):
    if name == 'ml-online':
        subprocess.run(['pip', 'uninstall', 'ml-online', '--yes'], check=True)
        subprocess.run(['pip', 'install', 'projects/ml-online'], check=True)

    subprocess.run([
        'soopervisor',
        'export-airflow',
        '--root',
        f'projects/{name}',
        '--output',
        '.',
    ],
                   check=True)

    subprocess.run(['python', f'dags/{name}.py'], check=True)


def test_export_airflow(monkeypatch, tmp_sample_project):
    export.project(project_root='.', output_path='exported')
    monkeypatch.syspath_prepend('exported/dags')
    airflow_home = Path(tmp_sample_project, 'exported').resolve()
    monkeypatch.setenv('AIRFLOW_HOME', airflow_home)
    mod = importlib.import_module('sample_project')
    dag = mod.dag

    assert isinstance(dag, DAG)
    assert set(dag.task_dict) == {'clean', 'plot', 'raw'}
    assert set(type(t) for t in dag.tasks) == {BashOperator}
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'raw': set(),
                'clean': {'raw'},
                'plot': {'clean'}
            }


def test_export_airflow_callables(monkeypatch, tmp_callables):
    export.project(project_root='.', output_path='exported')
    monkeypatch.syspath_prepend('exported/dags')
    airflow_home = Path(tmp_callables, 'exported').resolve()
    monkeypatch.setenv('AIRFLOW_HOME', airflow_home)
    mod = importlib.import_module('callables')
    dag = mod.dag

    script_cfg = ScriptConfig.from_project('exported/ploomber/callables')
    scripts = {
        t: script_cfg.to_script(command=f'ploomber task {t}')
        for t in dag.task_dict
    }

    assert isinstance(dag, DAG)
    # check tasks in dag
    assert set(dag.task_dict) == {'features', 'fit.py', 'get', 'join'}
    # check task's class
    assert set(type(t) for t in dag.tasks) == {BashOperator}
    # check dependencies
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'get': set(),
                'features': {'get'},
                'join': {'features', 'get'},
                'fit.py': {'join'}
            }

    # check generated scripts
    assert scripts['get'] == dag.task_dict['get'].bash_command
    assert scripts['features'] == dag.task_dict['features'].bash_command
    assert scripts['fit.py'] == dag.task_dict['fit.py'].bash_command
    assert scripts['join'] == dag.task_dict['join'].bash_command


def test_export_airflow_no_airflow_env(tmp_callables, capsys):
    Path('env.airflow.yaml').unlink()
    export.project(project_root='.', output_path='exported')

    assert 'No env.airflow.yaml found...' in capsys.readouterr().out
