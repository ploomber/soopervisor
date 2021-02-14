"""
Export a Ploomber DAG to Airflow
"""
import os
import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined
from ploomber.spec import DAGSpec

from soopervisor.airflow.config import AirflowConfig
from soopervisor.base.config import ScriptConfig


def project(project_root, output_path=None):
    """Export Ploomber project to Airflow

    Calling this function generates an Airflow DAG definition at
    {airflow-home}/dags/{project-name}.py and copies the project's source code
    to {airflow-home}/ploomber/{project-name}. The exported Airflow DAG is
    composed of BashOperator tasks, one per task in the Ploomber DAG.

    Parameters
    ----------
    project_root : str
        Project's root folder (pipeline.yaml parent)

    output_path : str, optional
        Output folder. If None, it looks up the value in the
        AIRFLOW_HOME environment variable. If the variable isn't set, it
        defaults to ~/airflow
    """
    env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                      undefined=StrictUndefined)
    template = env.get_template('airflow.py')

    project_root = Path(project_root).resolve()

    # validate the project passses soopervisor checks
    AirflowConfig.from_project(project_root)

    # use airflow-home to know where to save the Airflow dag definition
    if output_path is None:
        output_path = os.environ.get('AIRFLOW_HOME', '~/airflow')

    output_path = str(Path(output_path).expanduser())

    Path(output_path).mkdir(exist_ok=True, parents=True)

    print('Processing project: ', project_root)

    # copy project-root to airflow-home (create a folder with the same name)
    # TODO: what to exclude?
    project_name = Path(project_root).name
    project_root_airflow = Path(output_path, 'ploomber', project_name)
    project_root_airflow.mkdir(exist_ok=True, parents=True)

    out = template.render(project_root=project_root_airflow,
                          project_name=project_name)

    if project_root_airflow.exists():
        print(f'Removing existing project at {project_root_airflow}')
        shutil.rmtree(project_root_airflow)

    print('Exporting...')

    # make sure this works if copying everything in a project root
    # sub-directory
    try:
        rel = project_root_airflow.resolve().relative_to(project_root)
        sub_dir = rel.parts[0]
        is_sub_dir = True
    except ValueError:
        is_sub_dir = False
        sub_dir = None

    if is_sub_dir:

        def ignore(src, names):
            dir_name = Path(src).resolve().relative_to(project_root)
            return names if str(dir_name).startswith(sub_dir) else []

        shutil.copytree(project_root, dst=project_root_airflow, ignore=ignore)
    else:
        shutil.copytree(project_root, dst=project_root_airflow)

    # delete env.yaml and rename env.airflow.yaml
    env_airflow = Path(project_root_airflow / 'env.airflow.yaml')

    if env_airflow.exists():
        env_yaml = Path(project_root_airflow / 'env.yaml')

        if env_yaml.exists():
            env_yaml.unlink()

        env_airflow.rename(env_yaml)
    else:
        print('No env.airflow.yaml found...')

    # generate script that exposes the DAG airflow
    path_out = Path(output_path, 'dags', project_name + '.py')
    path_out.parent.mkdir(exist_ok=True, parents=True)
    path_out.write_text(out)

    print('Copied project source code to: ', project_root_airflow)
    print('Saved Airflow DAG definition to: ', path_out)


def spec_to_airflow(project_root, dag_name, airflow_default_args):
    """Initialize a Soopervisor project DAG and convert it to Airflow

    Notes
    -----
    This function is called by the DAG definition parsed by Airflow in
    {AIRFLOW_HOME}/dags
    """
    script_cfg = ScriptConfig.from_project(project_root)

    # NOTE: we use lazy_import=True here because this runs in the
    # airflow host and we should never expect that environment to have
    # the project environment configured, as its only purpose is to parse
    # the DAG
    dag = DAGSpec(script_cfg.paths.entry_point, lazy_import=True).to_dag()

    return _dag_to_airflow(dag, dag_name, script_cfg, airflow_default_args)


def _dag_to_airflow(dag, dag_name, script_cfg, airflow_default_args):
    """Convert a Ploomber DAG to an Airflow DAG

    Notes
    -----
    This function is called by the DAG definition parsed by Airflow in
    {AIRFLOW_HOME}/dags
    """
    # airflow *is not* a soopervisor dependency, moving the imports here to
    # prevent module not found errors for users who don't use airflow
    from airflow import DAG
    from airflow.operators.bash_operator import BashOperator

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
