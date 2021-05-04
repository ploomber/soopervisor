from pathlib import Path

import yaml
import click

from soopervisor import __version__
from soopervisor.build import build_project
from soopervisor.argo.config import ArgoConfig
from soopervisor.airflow import export as export_airflow_module
from soopervisor.argo import export as export_argo
from soopervisor.aws import lambda_, batch
from soopervisor import config


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    CLI
    """
    pass


@cli.command()
@click.option('--clean-products-path',
              '-c',
              is_flag=True,
              help='Remove all files from product_root before building')
@click.option('--dry-run',
              '-d',
              is_flag=True,
              help='Prepare execution without actually doing it')
@click.option('--load-dag/--no-load-dag',
              default=False,
              help='Whether to load dag for validation purposes')
def build(clean_products_path, dry_run, load_dag):
    """
    Build project
    """
    build_project(project_root='.',
                  clean_products_path=clean_products_path,
                  dry_run=dry_run,
                  load_dag=load_dag)


@cli.command()
@click.option('--upload',
              '-u',
              is_flag=True,
              help='Upload code, assumes "kubectl" is properly configured')
@click.option(
    '--root',
    '-r',
    type=str,
    help="Project's root path, defaults to current working directory",
    default='.')
def export(upload, root):
    """
    Export to Argo (Kubernetes)
    """
    config = ArgoConfig.from_project(project_root=root)

    if upload:
        export_argo.upload_code(config)

    click.echo('Generating argo spec from project...')
    export_argo.project(config)
    click.echo('Done. Saved argo spec to "argo.yaml"')

    click.echo('Submit your workflow with: argo submit -n argo argo.yaml')


@cli.command()
@click.option('--output',
              '-o',
              type=str,
              help='Output path, if empty looks for env var AIRFLOW_HOME, '
              'if undefined, uses ~/airflow',
              default=None)
@click.option(
    '--root',
    '-r',
    type=str,
    help="Project's root path, defaults to current working directory",
    default='.')
def export_airflow(output, root):
    """
    Export to Apache Airflow
    """
    click.echo('Exporting to Airflow...')
    export_airflow_module.project(project_root=root, output_path=output)


@cli.command()
@click.argument('name')
@click.option('--backend',
              '-b',
              type=click.Choice(['aws-lambda', 'aws-batch']),
              required=True)
def add(name, backend):
    """Add an environment
    """
    if Path('soopervisor.yaml').exists():
        cfg = yaml.load(Path('soopervisor.yaml').read_text())

        if name in cfg:
            raise click.ClickException(f'A {name!r} section in the '
                                       'soopervisor.yaml configuration file '
                                       'already exists. Choose another name.')

    if not Path('setup.py').exists():
        raise click.ClickException('Only packages with a setup.py file are '
                                   'supported. Tip: run "ploomber scaffold" '
                                   'to create a base project')

    if Path(name).exists():
        raise click.ClickException(f'{name!r} already exists. '
                                   'Select a different name.')

    if backend == 'aws-batch':
        batch.add(name=name)
    else:
        lambda_.add(name=name)


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

    backend = config.get_backend(name)

    if backend == 'aws-batch':
        batch.submit(name=name, until=until)
    else:
        lambda_.submit(name=name, until=until)


if __name__ == '__main__':
    cli()
