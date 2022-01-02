import json
from pathlib import Path

from kubernetes.client import models as k8s

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

volume = k8s.V1Volume(name='shared-folder', host_path=dict(path='/host'))
volume_mount = k8s.V1VolumeMount(mount_path='/mnt/shared-folder',
                                 name='shared-folder')

default_args = {
    'start_date': days_ago(0),
}

dag = DAG(
    dag_id='ml-intermediate',
    default_args=default_args,
    description='Ploomber DAG (ml-intermediate)',
    schedule_interval=None,
)

path_to_spec = Path(__file__).parent / 'ml-intermediate.json'
spec = json.loads(path_to_spec.read_text())

for task in spec['tasks']:
    KubernetesPodOperator(image=spec['image'],
                          cmds=['bash', '-cx'],
                          arguments=[task['command']],
                          dag=dag,
                          task_id=task['name'],
                          name='ml-intermediate-pod',
                          in_cluster=False,
                          do_xcom_push=False,
                          namespace='default',
                          image_pull_policy='Never',
                          volumes=[volume],
                          volume_mounts=[volume_mount])

for task in spec['tasks']:
    t = dag.get_task(task['name'])

    for upstream in task['upstream']:
        t.set_upstream(dag.get_task(upstream))
