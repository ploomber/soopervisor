import click

from soopervisor.build import build_project
from soopervisor.storage.box import BoxUploader


@click.group()
def cli():
    """
    CLI
    """
    pass


@cli.command()
@click.option('--clean-products-path',
              is_flag=True,
              help='Remove all files from product_root before building')
def build(clean_products_path):
    """
    Build project
    """
    build_project(project_root='.', clean_products_path=clean_products_path)


@cli.command()
@click.argument('directory')
def upload(directory, help='Directory to upload'):
    """
    Upload files
    """
    uploader = BoxUploader.from_environ()
    uploader.upload_files([directory])


if __name__ == '__main__':
    cli()
