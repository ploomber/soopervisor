from pathlib import Path

from soopervisor.airflow.export import spec_to_airflow
from airflow.utils.dates import days_ago

default_args = {
    'start_date': days_ago(0),
}

# this file should go in dags/ but the project's source code should go
# in a ploomber/ folder at the same level
project_root = str(
    Path(__file__, '..', '..', 'ploomber', '{{project_name}}').resolve())

dag = spec_to_airflow(project_root=project_root,
                      dag_name='{{project_name}}',
                      airflow_default_args=default_args)
