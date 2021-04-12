import click

from soopervisor import __version__
from soopervisor.build import build_project
from soopervisor.argo.config import ArgoConfig
from soopervisor.airflow import export as export_airflow_module
from soopervisor.argo import export as export_argo
from soopervisor.aws import lambda_


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
def export_aws_lambda():
    """
    Export to AWS Lambda for online inference
    """
    lambda_.main()


if __name__ == '__main__':
    cli()
