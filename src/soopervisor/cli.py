from pathlib import Path

import yaml
import click

from soopervisor import __version__
from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.airflow.export import AirflowExporter
from soopervisor.aws import lambda_, batch
from soopervisor import config
from soopervisor.enum import Backend


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    soopervisor exports ploomber projects to run in other platforms
    """
    pass


@cli.command()
@click.argument('name')
@click.option('--backend',
              '-b',
              type=click.Choice(Backend.get_values()),
              required=True)
def add(name, backend):
    """Add an environment
    """
    backend = Backend(backend)

    if Path('soopervisor.yaml').exists():
        cfg = yaml.load(Path('soopervisor.yaml').read_text())

        if name in cfg:
            raise click.ClickException(f'A {name!r} section in the '
                                       'soopervisor.yaml configuration file '
                                       'already exists. Choose another name.')

    if not Path('setup.py').exists() and backend in {
            Backend.aws_batch, Backend.aws_lambda
    }:
        raise click.ClickException('Only packages with a setup.py file are '
                                   f'supported when using {backend!r}. '
                                   'Suggestion: run "ploomber scaffold" '
                                   'to create a base project')

    if Path(name).exists():
        raise click.ClickException(f'{name!r} already exists. '
                                   'Select a different name.')

    if backend == Backend.aws_batch:
        batch.add(name=name)

    elif backend == Backend.aws_lambda:
        lambda_.add(name=name)

    elif backend == Backend.argo_workflows:
        # TODO: re-enable support for upload
        # export_argo.upload_code(config)
        exporter = ArgoWorkflowsExporter('soopervisor.yaml', env_name=name)
        exporter.add()

    elif backend == Backend.airflow:
        click.echo('Exporting to Airflow...')
        exporter = AirflowExporter('soopervisor.yaml', env_name=name)
        exporter.add()


@cli.command()
@click.argument('name')
@click.option('--until-build',
              '-ub',
              is_flag=True,
              help='Only build docker image')
def submit(name, until_build):
    """
    Submit an environment for execution/deployment
    """
    until = None

    if until_build:
        until = 'build'

    backend = Backend(config.get_backend(name))

    if backend == Backend.aws_batch:
        batch.submit(name=name, until=until)
    elif backend == Backend.aws_lambda:
        lambda_.submit(name=name, until=until)
    elif backend == Backend.airflow:
        raise click.ClickException(
            f'Submitting environments with {backend} backend is not '
            'supported, you must copy the exported environment to AIRFLOW_HOME'
        )
    elif backend == Backend.argo_workflows:
        raise click.ClickException(
            f'Submitting environments with {backend} backend is not '
            'supported, submit your workflow using the "argo submit" command')


if __name__ == '__main__':
    cli()
