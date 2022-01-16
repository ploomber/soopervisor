"""
Export to Argo Workflows
"""
from pathlib import Path

import click
from ploomber.io._commander import Commander, CommanderStop
import yaml
from yaml.representer import SafeRepresenter

try:
    import importlib.resources as pkg_resources
except ImportError:
    # if python<3.7
    import importlib_resources as pkg_resources

from soopervisor import assets
from soopervisor import abc
from soopervisor.commons import docker
from soopervisor import commons
from soopervisor.argo.config import ArgoConfig


class ArgoWorkflowsExporter(abc.AbstractExporter):
    CONFIG_CLASS = ArgoConfig

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @staticmethod
    def _add(cfg, env_name):
        """
        Add Dockerfile
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('argo-workflows/Dockerfile',
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists())
            e.success('Done')

    @staticmethod
    def _export(cfg, env_name, mode, until, skip_tests, ignore_git):
        """
        Build and upload Docker image. Export Argo YAML spec.
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:

            tasks, args = commons.load_tasks(cmdr=cmdr,
                                             name=env_name,
                                             mode=mode)

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            pkg_name, target_image = docker.build(cmdr,
                                                  cfg,
                                                  env_name,
                                                  until=until,
                                                  entry_point=args[1],
                                                  skip_tests=skip_tests,
                                                  ignore_git=ignore_git)

            cmdr.info('Generating Argo Workflows YAML spec')
            _make_argo_spec(tasks=tasks,
                            args=args,
                            env_name=env_name,
                            cfg=cfg,
                            pkg_name=pkg_name,
                            target_image=target_image)

            cmdr.success('Done.')


# TODO: delete
class _literal_str(str):
    """Custom str to represent it in YAML literal style
    Source: https://stackoverflow.com/a/20863889/709975
    """
    pass


def _change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar

    return new_representer


# configure yaml to represent "literal_str" objects in literal style
represent_literal_str = _change_style('|', SafeRepresenter.represent_str)
yaml.add_representer(_literal_str, represent_literal_str)


def _make_argo_task(name, dependencies):
    """Generate an Argo Task spec
    """
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


def _make_argo_spec(tasks, args, env_name, cfg, pkg_name, target_image):
    """Generate Argo's YAML spec
    """
    if cfg.mounted_volumes:
        volumes, volume_mounts = zip(*((mv.to_volume(), mv.to_volume_mount())
                                       for mv in cfg.mounted_volumes))
        # force them to be lists to prevent "!!python/tuple" to be added
        volumes = list(volumes)
        volume_mounts = list(volume_mounts)
    else:
        volumes = []
        volume_mounts = []

    argo_spec = yaml.safe_load(
        pkg_resources.read_text(assets, 'argo-workflow.yaml'))
    argo_spec['spec']['volumes'] = volumes

    tasks_specs = []

    for task_name, upstream in tasks.items():
        spec = _make_argo_task(task_name, upstream)
        tasks_specs.append(spec)

    argo_spec['metadata']['generateName'] = f'{pkg_name}-'.replace('_', '-')
    argo_spec['spec']['templates'][1]['dag']['tasks'] = tasks_specs

    script = argo_spec['spec']['templates'][0]['script']
    script['volumeMounts'] = volume_mounts
    script['image'] = target_image

    if cfg.repository is None:
        click.echo('null repository found in soopervisor.yaml, '
                   'setting imagePullPolicy to "Never"')
        script['imagePullPolicy'] = 'Never'

    command = 'ploomber task {{inputs.parameters.task_name}}'

    if args:
        command = f'{command} {" ".join(args)}'

    # use literal_str to make the script source code be represented in YAML
    # literal style, this makes it readable
    script['source'] = _literal_str(command)

    # when we run this the current working directory is env_name/
    with open('argo.yaml', 'w') as f:
        yaml.dump(argo_spec, f)

    output_path = f'{env_name}/argo.yaml'
    click.echo(f'Done. Saved argo spec to {output_path!r}')
    click.echo(f'Submit your workflow with: argo submit -n argo {output_path}')

    return argo_spec
