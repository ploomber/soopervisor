import shutil
from pathlib import Path
import subprocess

import pytest
from airflow.utils.dates import days_ago

from soopervisor import export


def test_export_airflow(monkeypatch, tmp_empty):
    airflow_home = str(Path(tmp_empty, 'airflow-home'))
    airflow_home = str(Path('~/airflow').expanduser())
    shutil.rmtree(airflow_home)
    monkeypatch.setenv('AIRFLOW_HOME', airflow_home, prepend=False)

    subprocess.run(['airflow', 'initdb'], check=True)
    Path(airflow_home, 'dags').mkdir()

    subprocess.run([
        'git', 'clone', '--branch', 'dev',
        'https://github.com/ploomber/projects'
    ],
                   check=True)

    export.to_airflow('projects/ml-intermediate')

    pweb = subprocess.Popen(['airflow', 'webserver', '-p', '8086'])
    # p = subprocess.Popen(['airflow', 'scheduler'])

    import time
    time.sleep(30)

    # from IPython import embed
    # embed()

    # subprocess.run(['airflow', 'list_dags'], check=True)
    # unpause
    subprocess.run(['airflow', 'trigger_dag', 'ml-intermediate'], check=True)

    # p.kill()
    pweb.kill()
    # p.wait()
    pweb.wait()
