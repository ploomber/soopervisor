import click

from soopervisor.build import build_project
from soopervisor.argo.config import ArgoConfig
from soopervisor.airflow import export as export_airflow_module
from soopervisor.argo import export as export_argo


@click.group()
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
def export(upload):
    """
    Export Ploomber project to Argo (Kubernetes)
    """
    config = ArgoConfig.from_project(project_root='.')

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
def export_airflow(output):
    """
    Export Ploomber project to Apache Airflow
    """
    click.echo('Exporting to Airflow...')
    export_airflow_module.project(project_root='.', output_path=output)


if __name__ == '__main__':
    cli()
