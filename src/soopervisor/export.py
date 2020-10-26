"""
Export a Ploomber DAG to Airflow
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

from ploomber.spec import DAGSpec
from soopervisor.script.ScriptConfig import ScriptConfig


def spec_to_airflow(project_root):
    script_cfg = ScriptConfig.from_path(project_root)
    # Replace the project root to reflect the new location - or maybe just
    # write a soopervisor.yaml, then we can we rid of this line
    script_cfg.paths.project = project_root

    # TODO: use lazy_import from script_cfg
    dag = DAGSpec(f'{project_root}/pipeline.yaml', lazy_import=True).to_dag()

    return _dag_to_airflow(dag)


def _dag_to_airflow(dag, script_cfg, airflow_default_args):
    dag_airflow = DAG(
        dag.name.replace(' ', '-'),
        default_args=airflow_default_args,
        description='Ploomber dag',
        schedule_interval=None,
    )

    for task_name in dag:
        task_airflow = BashOperator(task_id=task_name,
                                    bash_command=script_cfg.to_script(
                                        command=f'ploomber task {task_name}'),
                                    dag=dag_airflow)

    for task_name in dag:
        task_ploomber = dag[task_name]
        task_airflow = dag_airflow.get_task(task_name)

        for upstream in task_ploomber.upstream:
            task_airflow.set_upstream(dag_airflow.get_task(upstream))

    return dag_airflow
