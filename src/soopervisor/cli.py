from pathlib import Path

import yaml
import click

from soopervisor import __version__
from soopervisor import config
from soopervisor import exporter
from soopervisor.enum import Backend


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
        cfg = yaml.load(Path('soopervisor.yaml').read_text())

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
def export(name, until_build):
    """
    Export a target platform for execution/deployment
    """
    until = None

    if until_build:
        until = 'build'

    backend = Backend(config.get_backend(name))
    Exporter = exporter.for_backend(backend)
    Exporter('soopervisor.yaml', env_name=name).export(until=until)


if __name__ == '__main__':
    cli()
