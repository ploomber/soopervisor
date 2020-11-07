"""
Template to convert a Ploomber DAG to Airflow
"""
from pathlib import Path
import os

from soopervisor.airflow.export import spec_to_airflow
from airflow.utils.dates import days_ago

default_args = {
    'start_date': days_ago(0),
}

AIRFLOW_HOME = os.environ.get('AIRFLOW_HOME',
                              str(Path('~/airflow').expanduser()))
project_root = str(Path(AIRFLOW_HOME, 'ploomber', '{{project_name}}'))

dag = spec_to_airflow(project_root=project_root,
                      dag_name='{{project_name}}',
                      airflow_default_args=default_args)
