import os
import subprocess
from pathlib import Path
import importlib

from airflow import DAG
from airflow.operators.bash import BashOperator
import pytest

from soopervisor.airflow.export import AirflowExporter
from soopervisor.base.config import ScriptConfig


@pytest.mark.parametrize(
    'name',
    [
        'ml-intermediate',
        'etl',
        'ml-online',
    ],
)
def test_generate_valid_airflow_dags(name, tmp_projects):
    # TODO: clean up projects/ and remove the soopervisor.yaml, they should
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


def test_export_airflow_sample_project(monkeypatch, tmp_sample_project,
                                       no_sys_modules_cache):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')
    exporter.add()

    monkeypatch.syspath_prepend('serve/dags')
    airflow_home = Path(tmp_sample_project, 'serve').resolve()
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


def test_export_airflow_custom_args(monkeypatch, tmp_sample_project,
                                    no_sys_modules_cache):
    Path('soopervisor.yaml').write_text('serve:\n    args: --some-arg')

    # export project
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')
    exporter.add()

    # load exported dag
    monkeypatch.syspath_prepend('serve/dags')
    airflow_home = str(Path(tmp_sample_project, 'serve').resolve())
    monkeypatch.setenv('AIRFLOW_HOME', airflow_home)
    mod = importlib.import_module('sample_project')
    dag = mod.dag

    assert 'ploomber task raw --some-arg' in dag.task_dict['raw'].bash_command
    assert 'ploomber task clean --some-arg' in dag.task_dict[
        'clean'].bash_command
    assert 'ploomber task plot --some-arg' in dag.task_dict[
        'plot'].bash_command


def test_export_airflow_callables(monkeypatch, tmp_callables):
    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')
    exporter.add()

    monkeypatch.syspath_prepend('serve/dags')
    airflow_home = Path(tmp_callables, 'serve').resolve()
    monkeypatch.setenv('AIRFLOW_HOME', airflow_home)
    mod = importlib.import_module('callables')
    dag = mod.dag

    # generate scripts to compare them to the ones in airflow
    script_cfg = ScriptConfig.from_file_with_root_key(
        path_to_config='serve/ploomber/callables/soopervisor.yaml',
        env_name='serve')
    scripts = {
        t: script_cfg.to_script(command=f'ploomber task {t}')
        for t in dag.task_dict
    }

    assert isinstance(dag, DAG)
    # check tasks in dag
    assert set(dag.task_dict) == {'features', 'fit', 'get', 'join'}
    # check task's class
    assert set(type(t) for t in dag.tasks) == {BashOperator}
    # check dependencies
    assert {n: t.upstream_task_ids
            for n, t in dag.task_dict.items()} == {
                'get': set(),
                'features': {'get'},
                'join': {'features', 'get'},
                'fit': {'join'}
            }

    # check generated scripts
    assert scripts['get'] == dag.task_dict['get'].bash_command
    assert scripts['features'] == dag.task_dict['features'].bash_command
    assert scripts['fit'] == dag.task_dict['fit'].bash_command
    assert scripts['join'] == dag.task_dict['join'].bash_command


def test_export_airflow_no_airflow_env(tmp_callables, capsys):
    Path('env.airflow.yaml').unlink()

    exporter = AirflowExporter(path_to_config='soopervisor.yaml',
                               env_name='serve')
    exporter.add()

    assert 'No env.airflow.yaml found...' in capsys.readouterr().out


# TODO: add test when there is no config file