"""
Template to convert a Ploomber DAG to Airflow
"""
from airflow.utils.dates import days_ago

from soopervisor.export import spec_to_airflow

default_args = {
    'start_date': days_ago(0),
}

dag = spec_to_airflow(project_root='{{project_root}}',
                      project_name='{{project_name}}',
                      airflow_default_args=default_args)
