"""
Export a Ploomber DAG to Argo/Airflow
"""
import os
import shutil
from pathlib import Path
import subprocess
try:
    import importlib.resources as pkg_resources
except ImportError:
    # if python<3.7
    import importlib_resources as pkg_resources

import yaml
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from jinja2 import Environment, PackageLoader, StrictUndefined

from ploomber.spec import DAGSpec
from soopervisor.script.ScriptConfig import AirflowConfig, ScriptConfig
from soopervisor import assets


def _make_argo_task(name, dependencies):
    task = {
        'name': name,
        'dependencies': dependencies,
        'template': 'run-task',
        'arguments': {
            'parameters': [{
                'name': 'task_name',
                'value': name,
            }]
        }
    }
    return task


def upload_code(project_root):

    print('Locating nfs-server pod...')
    result = subprocess.run([
        'kubectl', 'get', 'pods', '-l', 'role=nfs-server', '-o',
        'jsonpath="{.items[0].metadata.name}"'
    ],
                            check=True,
                            capture_output=True)

    pod_name = result.stdout.decode('utf-8').replace('"', '')
    project_name = Path(project_root).resolve().name

    print('Uploading code...')
    subprocess.run([
        'kubectl', 'cp',
        str(project_root), f'{pod_name}:/exports/{project_name}'
    ])


def to_argo(project_root):
    # TODO: validate project first
    # TODO: use lazy_import from script_cfg
    dag = DAGSpec(f'{project_root}/pipeline.yaml', lazy_import=True).to_dag()

    d = yaml.safe_load(pkg_resources.read_text(assets, 'argo-workflow.yaml'))

    tasks_specs = []

    for task_name in dag:
        task = dag[task_name]
        spec = _make_argo_task(task_name, list(task.upstream))
        tasks_specs.append(spec)

    project_name = Path(project_root).resolve().name

    d['metadata']['generateName'] = f'{project_name}-'
    d['spec']['templates'][1]['dag']['tasks'] = tasks_specs
    d['spec']['templates'][0]['script']['volumeMounts'][0][
        'subPath'] = project_name

    with open(f'{project_root}/argo.yaml', 'w') as f:
        yaml.dump(d, f)

    return d


def to_airflow(project_root):
    """Convert a Soopervisor project to an Airflow one
    """
    env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                      undefined=StrictUndefined)
    template = env.get_template('airflow.py')

    project_root = Path(project_root).resolve()

    # validate the project passses soopervisor checks
    config = AirflowConfig.from_path(project_root)
    config.validate()

    # use airflow-home to know where to save the Airflow dag definition
    airflow_home = os.environ.get('AIRFLOW_HOME', '~/airflow')
    airflow_home = str(Path(airflow_home).expanduser())

    print('Processing project: ', project_root)

    # copy project-root to airflow-home (create a folder with the same name)
    # TODO: what to exclude?
    project_name = Path(project_root).name
    project_root_airflow = Path(airflow_home, 'ploomber', project_name)

    out = template.render(project_root=project_root_airflow,
                          project_name=project_name)

    if project_root_airflow.exists():
        print('Removing existing project')
        shutil.rmtree(project_root_airflow)

    shutil.copytree(project_root, dst=project_root_airflow)

    # delete env.yaml and rename env.airflow.yaml
    env_yaml = Path(project_root_airflow / 'env.yaml')
    env_yaml.unlink()
    Path(project_root_airflow / 'env.airflow.yaml').rename(env_yaml)

    # generate script that exposes the DAG airflow
    path_out = Path(airflow_home, 'dags', project_name + '.py')
    path_out.write_text(out)

    print('Copied project source code to: ', project_root_airflow)
    print('Saved Airflow DAG definition to: ', path_out)


def spec_to_airflow(project_root, project_name, airflow_default_args):
    """Initialize a Soopervisor project DAG and convert it to Airflow

    Notes
    -----
    This function is called by the DAG definition parsed by Airflow in
    {AIRFLOW_HOME}/dags
    """
    script_cfg = ScriptConfig.from_path(project_root)
    # Replace the project root to reflect the new location - or maybe just
    # write a soopervisor.yaml, then we can we rid of this line
    script_cfg.paths.project = project_root

    # TODO: use lazy_import from script_cfg
    dag = DAGSpec(f'{project_root}/pipeline.yaml', lazy_import=True).to_dag()

    return _dag_to_airflow(dag, project_name, script_cfg, airflow_default_args)


def _dag_to_airflow(dag, dag_name, script_cfg, airflow_default_args):
    """Convert a Ploomber DAG to an Airflow DAG

    Notes
    -----
    This function is called by the DAG definition parsed by Airflow in
    {AIRFLOW_HOME}/dags
    """
    dag_airflow = DAG(
        dag_name,
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
