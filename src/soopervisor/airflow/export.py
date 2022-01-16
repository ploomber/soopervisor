"""
Export a Ploomber DAG to Airflow
"""
import json
import os
from pathlib import Path

import click

from ploomber.io._commander import Commander, CommanderStop
from soopervisor.airflow.config import AirflowConfig
from soopervisor import commons
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
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists())

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
    def _export(cfg, env_name, mode, until, skip_tests, ignore_git):
        """
        Copies the current source code to the target environment folder.
        The code along with the DAG declaration file can be copied to
        AIRFLOW_HOME for execution
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            tasks, args = commons.load_tasks(cmdr=e, name=env_name, mode=mode)

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            pkg_name, target_image = commons.docker.build(
                e,
                cfg,
                env_name,
                until=until,
                entry_point=args[1],
                skip_tests=skip_tests,
                ignore_git=ignore_git)

            dag_dict = generate_airflow_spec(tasks, args, target_image)

            path_dag_dict_out = Path(pkg_name + '.json')
            path_dag_dict_out.write_text(json.dumps(dag_dict))


def generate_airflow_spec(tasks, args, target_image):
    """
    Generates a dictionary with the spec used by Airflow to construct the
    DAG
    """
    dag_dict = dict(tasks=[], image=target_image)

    for name, upstream in tasks.items():
        command = f'ploomber task {name}'

        if args:
            command = f'{command} {" ".join(args)}'

        dag_dict['tasks'].append({
            'name': name,
            'upstream': upstream,
            'command': command
        })

    return dag_dict
