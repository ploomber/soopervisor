from pathlib import Path

import yaml
import click

from soopervisor import __version__
from soopervisor import config
from soopervisor import exporter
from soopervisor.enum import Backend, Mode


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Soopervisor exports Ploomber projects.

    Example (export to Argo Workflows for training):

    $ soopervisor add training --backend argo-workflows

    $ soopervisor export training

    """
    pass


@cli.command()
@click.argument('name')
@click.option('--backend',
              '-b',
              type=click.Choice(Backend.get_values()),
              required=True)
def add(name, backend):
    """Add a new target platform
    """
    backend = Backend(backend)

    if Path('soopervisor.yaml').exists():
        cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())

        if name in cfg:
            raise click.ClickException(f'A {name!r} section in the '
                                       'soopervisor.yaml configuration file '
                                       'already exists. Choose another name.')

    if Path(name).exists():
        raise click.ClickException(f'{name!r} already exists. '
                                   'Select a different name.')

    Exporter = exporter.for_backend(backend)
    Exporter('soopervisor.yaml', env_name=name).add()


@cli.command()
@click.argument('name')
@click.option('--until-build',
              '-ub',
              is_flag=True,
              help='Only build docker image')
@click.option('--skip-tests',
              '-s',
              is_flag=True,
              help='Skip docker image tests')
@click.option('--mode',
              '-m',
              type=click.Choice(Mode.get_values()),
              default=Mode.incremental.value)
@click.option('--ignore-git',
              '-i',
              is_flag=True,
              help='Ignore git tracked files (include everything)')
def export(name, until_build, mode, skip_tests, ignore_git):
    """
    Export a target platform for execution/deployment
    """
    until = None

    if until_build:
        until = 'build'

    backend = Backend(config.get_backend(name))

    # TODO: warn on ignore-git if using SLURM (it's ignored)

    # TODO: ignore mode if using aws lambda, raised exception if value
    # is not the default
    if backend == Backend.aws_lambda:
        mode = None

    Exporter = exporter.for_backend(backend)
    Exporter('soopervisor.yaml', env_name=name).export(mode=mode,
                                                       until=until,
                                                       skip_tests=skip_tests,
                                                       ignore_git=ignore_git)


if __name__ == '__main__':
    cli()
