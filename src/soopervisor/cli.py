import click

from soopervisor.build import build_project
from soopervisor.storage.box import BoxUploader
from soopervisor import export as export_module


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
def build(clean_products_path, dry_run):
    """
    Build project
    """
    build_project(project_root='.',
                  clean_products_path=clean_products_path,
                  dry_run=dry_run)


@cli.command()
@click.argument('directory')
def upload(directory, help='Directory to upload'):
    """
    Upload files
    """
    uploader = BoxUploader.from_environ()
    uploader.upload_files([directory])


@cli.command()
@click.option('--upload', '-u', is_flag=True, help='Upload code')
def export(upload):
    """
    Export to argo
    """
    if upload:
        export_module.upload_code(project_root='.')

    print('Generating argo spec from project...')
    export_module.to_argo(project_root='.')
    print('Done. Saved argo spec to "argo.yaml"')

    print('Submit your workflow with: argo submit -n argo argo.yaml')


if __name__ == '__main__':
    cli()
