import importlib
from pathlib import Path

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from soopervisor.airflow import export


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

    assert isinstance(dag, DAG)
    assert set(dag.task_dict) == {'features', 'fit.py', 'get', 'join'}
    assert set(type(t) for t in dag.tasks) == {BashOperator}
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'get': set(),
                'features': {'get'},
                'join': {'features', 'get'},
                'fit.py': {'join'}
            }


def test_export_airflow_no_airflow_env(tmp_callables, capsys):
    Path('env.airflow.yaml').unlink()
    export.project(project_root='.', output_path='exported')

    assert 'No env.airflow.yaml found...' in capsys.readouterr().out
