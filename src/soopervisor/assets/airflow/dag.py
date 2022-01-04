import json
from pathlib import Path

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod \
    import KubernetesPodOperator

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
    KubernetesPodOperator(
        image=spec['image'],
        cmds=['bash', '-cx'],
        arguments=[task['command']],
        dag=dag,
        task_id=task['name'],
        name='{{project_name}}-pod',
        # if no File.client is configured, you may use volumes and
        # volume_mounts to share data among pods. See the tutorial in our
        # documentation for an example
        in_cluster=False,
        do_xcom_push=False,
        # if pulling a local image, set image_pull_policy='Never'
    )

for task in spec['tasks']:
    t = dag.get_task(task['name'])

    for upstream in task['upstream']:
        t.set_upstream(dag.get_task(upstream))
