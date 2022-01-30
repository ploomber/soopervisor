import json
from pathlib import Path

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.docker_operator import DockerOperator

default_args = {
    'start_date': days_ago(0),
}

dag = DAG(
    dag_id='{{project_name}}',
    default_args=default_args,
    description='Ploomber DAG ({{project_name}})',
    schedule_interval=None,
)

path_to_spec = Path(__file__).parent / '{{project_name}}.json'
spec = json.loads(path_to_spec.read_text())

for task in spec['tasks']:
    DockerOperator(
        image=spec['image'],
        command=task['command'],
        dag=dag,
        task_id=task['name'],
    )

for task in spec['tasks']:
    t = dag.get_task(task['name'])

    for upstream in task['upstream']:
        t.set_upstream(dag.get_task(upstream))
