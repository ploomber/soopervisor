"""
Export a Ploomber DAG to Airflow
"""
import os
import shutil
from pathlib import Path
from itertools import chain

import click
from jinja2 import Environment, PackageLoader, StrictUndefined

from ploomber.spec import DAGSpec
from soopervisor.airflow.config import AirflowConfig
from soopervisor.base.config import ScriptConfig
from ploomber.products import MetaProduct
from soopervisor import config
from soopervisor import abc


class AirflowExporter(abc.AbstractExporter):
    CONFIG_CLASS = AirflowConfig

    @staticmethod
    def _add(cfg, env_name):
        """Export Ploomber project to Airflow

        Calling this function generates an Airflow DAG definition at
        {airflow-home}/dags/{project-name}.py and copies the project's source
        code
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
        click.echo('Exporting to Airflow...')
        project_root = '.'
        output_path = env_name

        env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                          undefined=StrictUndefined)
        template = env.get_template('airflow.py')

        project_root = Path(project_root).resolve()

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
                              project_name=project_name,
                              env_name=env_name)

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

        # copy source code that will be uploadded
        if is_sub_dir:

            def ignore(src, names):
                dir_name = Path(src).resolve().relative_to(project_root)
                return names if str(dir_name).startswith(sub_dir) else []

            shutil.copytree(project_root,
                            dst=project_root_airflow,
                            ignore=ignore)
        else:
            shutil.copytree(project_root, dst=project_root_airflow)

        # generate script that exposes the DAG airflow
        path_out = Path(output_path, 'dags', project_name + '.py')
        path_out.parent.mkdir(exist_ok=True, parents=True)
        path_out.write_text(out)

        # rename env.{env_name}.yaml if needed
        config.replace_env(env_name=env_name, target_dir=project_root_airflow)

        print('Copied project source code to: ', project_root_airflow)
        print('Saved Airflow DAG definition to: ', path_out)

    @staticmethod
    def validate(cfg, dag, env_name):
        """
        Validates a project before exporting as an Airflow DAG.
        This runs as a sanity check in the development machine
        """
        project_root = Path(cfg.paths.project)

        env = (f'env.{env_name}.yaml'
               if Path(f'env.{env_name}.yaml').exists() else None)

        # TODO: let dagsspec figure out where to load pipeline.yaml from
        # NOTE: should lazy_import be an option from config?
        # check what would happen if we initialize the pipeline
        spec = DAGSpec(project_root / 'pipeline.yaml',
                       env=env,
                       lazy_import=True)
        dag_airflow = spec.to_dag()
        dag_airflow.render()

        # if factory function, check it's decorated to load from env.yaml (?)

        # with the dag instance and using env.airflow.yaml, check that products
        # are not saved inside the projects root folder
        #  airflow continuously scans $AIRFLOW_HOME/dags/ for dag definitions
        # and
        # any extra files can break this process - maybe also show the products
        # to know where things will be saved when running using airflow

        # TODO: test when some products aren't files
        products = [dag_airflow[t].product for t in dag_airflow._iter()]
        products = chain(*([p] if not isinstance(p, MetaProduct) else list(p)
                           for p in products))

        # TODO: improve error message by showing task names for each invalid
        # product

        def resolve_product(product):
            """Converts a File product to str with absolute path
            """
            return str(Path(str(product)).resolve())

        products_invalid = [
            # products cannot be inside project root, convert to absolute
            # otherwise /../../ might cause false positives
            str(p) for p in products
            if resolve_product(p).startswith(str(project_root))
        ]

        if products_invalid:
            products_invalid_ = '\n'.join(products_invalid)
            # TODO: replace {env} if None, must print the location of the
            # loaded env
            raise ValueError(
                f'The initialized DAG with "{env}" is '
                'invalid. Some products are located under '
                'the project\'s root folder, which is not allowed when '
                'deploying '
                'to Airflow. Modify your pipeline so all products are saved '
                f'outside the project\'s root folder "{project_root}". Fix '
                f'the following products:\n{products_invalid_}')

        # TODO: ignore non-files
        # TODO: also raise if relative paths - because we don't know where
        # the dag will be executed from

        # maybe instantiate with env.yaml and env.airflow.yaml to make sure
        # products don't clash?

        # check all products are prefixed with products root - this implies
        # that files should be absolute paths otherwise it's ambiguous -
        # should then we raise an arror if any product if defined with relative
        # paths?

    @staticmethod
    def _submit():
        raise NotImplementedError


def spec_to_airflow(project_root, dag_name, env_name, airflow_default_args):
    """Initialize a Soopervisor project DAG and convert it to Airflow

    Notes
    -----
    This function is called by the DAG definition parsed by Airflow in
    {AIRFLOW_HOME}/dags
    """
    script_cfg = ScriptConfig.from_file_with_root_key(
        Path(project_root, 'soopervisor.yaml'),
        env_name=env_name,
    )

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
