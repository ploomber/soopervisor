"""
Export a Ploomber DAG to Airflow
"""
import json
import os
from pathlib import Path

import click

from ploomber.spec import DAGSpec
from ploomber.io._commander import Commander
from soopervisor.airflow.config import AirflowConfig
from soopervisor.commons import docker
from soopervisor import abc


class AirflowExporter(abc.AbstractExporter):
    CONFIG_CLASS = AirflowConfig

    @staticmethod
    def _add(cfg, env_name):
        """Export Ploomber project to Airflow

        Generates a .py file that exposes a dag variable
        """
        click.echo('Exporting to Airflow...')
        project_root = Path('.').resolve()
        project_name = project_root.name

        # TODO: modify Dockerfile depending on package or non-package
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('airflow/dag.py',
                            project_name=project_name,
                            env_name=env_name)
            path_out = str(Path(env_name, project_name + '.py'))
            os.rename(Path(env_name, 'dag.py'), path_out)

            e.copy_template('airflow/Dockerfile',
                            conda=Path('environment.lock.yml').exists())

            click.echo(
                f'Airflow DAG declaration saved to {path_out!r}, you may '
                'edit the file to change the configuration if needed, '
                '(e.g., set the execution period)')

    @staticmethod
    def _validate(cfg, dag, env_name):
        """
        Validates a project before exporting as an Airflow DAG.
        This runs as a sanity check in the development machine
        """
        pass

    @staticmethod
    def _export(cfg, env_name, until):
        """
        Copies the current source code to the target environment folder.
        The code along with the DAG declaration file can be copied to
        AIRFLOW_HOME for execution
        """
        dag = DAGSpec.find(lazy_import=True).to_dag()

        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:

            pkg_name, target_image = docker.build(e,
                                                  cfg,
                                                  env_name,
                                                  until=until)

        dag_dict = dict(tasks=[], image=target_image)

        for name, task in dag.items():
            upstream = [t.name for t in task.upstream.values()]
            dag_dict['tasks'].append({'name': name, 'upstream': upstream})

        path_dag_dict_out = Path(env_name, pkg_name + '.json')
        path_dag_dict_out.write_text(json.dumps(dag_dict))
