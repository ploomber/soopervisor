import os
import subprocess
from pathlib import Path

import pytest

from soopervisor.airflow import export


@pytest.fixture(scope='module')
def tmp_projects(tmpdir_factory):
    old = os.getcwd()
    tmp_path = tmpdir_factory.mktemp('projects')
    os.chdir(str(tmp_path))
    subprocess.run(['git', 'clone', 'https://github.com/ploomber/projects'],
                   check=True)
    yield str(Path(tmp_path).resolve())
    os.chdir(old)


@pytest.mark.parametrize(
    'name',
    ['ml-intermediate', 'etl'],
)
def test_generate_valid_airflow_dags(name, tmp_projects):
    export.project(project_root=f'projects/{name}', output_path='.')
    subprocess.run(['python', f'dags/{name}.py'], check=True)
