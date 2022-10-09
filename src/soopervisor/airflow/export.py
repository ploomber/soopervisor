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
    """
    Airflow exporter, the generated Airflow DAG can be customized usin
    presets: 'none' (default, KubernetesPodOperator), bash (DockerOperator)
    """
    CONFIG_CLASS = AirflowConfig

    @staticmethod
    def _add(cfg, env_name):
        """Export Ploomber project to Airflow

        Generates a .py file that exposes a dag variable
        """
        click.echo('Exporting to Airflow...')
        project_root = Path('.').resolve()
        project_name = project_root.name

        name = f'{cfg.preset}.py'

        # TODO: modify Dockerfile depending on package or non-package
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template(f'airflow/{name}',
                            project_name=project_name,
                            env_name=env_name)
            path_out = str(Path(env_name, project_name + '.py'))
            os.rename(Path(env_name, name), path_out)

            if cfg.preset != 'bash':
                e.copy_template('docker/Dockerfile',
                                conda=Path('environment.lock.yml').exists(),
                                setup_py=Path('setup.py').exists(),
                                lib=Path('lib').exists(),
                                env_name=env_name)

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
    def _export(cfg, env_name, mode, until, skip_tests, skip_docker,
                ignore_git, lazy_import, task_name):
        """
        Copies the current source code to the target environment folder.
        The code along with the DAG declaration file can be copied to
        AIRFLOW_HOME for execution
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            tasks, args = commons.load_tasks(cmdr=e,
                                             name=env_name,
                                             mode=mode,
                                             lazy_import=lazy_import,
                                             task_name=task_name)

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            # TODO: throw a warning if non-docker preset but there is a
            # Dockerfile
            if cfg.preset != 'bash' and not skip_docker:
                pkg_name, target_image = commons.docker.build(
                    e,
                    cfg,
                    env_name,
                    until=until,
                    entry_point=args[1],
                    skip_tests=skip_tests,
                    ignore_git=ignore_git)
                target_image = target_image[
                    commons.dependencies.get_default_image_key()]
                dag_dict = generate_airflow_spec(tasks, args, target_image)

                path_dag_dict_out = Path(pkg_name + '.json')
                path_dag_dict_out.write_text(json.dumps(dag_dict))

            else:
                (pkg_name, target_image
                 ) = commons.source.find_package_name_and_version()

                dag_dict = generate_airflow_spec(tasks, args, target_image)
                path_dag_dict_out = Path(env_name, pkg_name + '.json')
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
