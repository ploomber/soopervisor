import click

from ploomberci.build import build_project
from ploomberci.storage.box import BoxUploader


@click.group()
def cli():
    """
    CLI
    """
    pass


@cli.command()
@click.option('--clean-product-root',
              is_flag=True,
              help='Remove all files from product_root before building')
def build(clean_product_root):
    """
    Build project
    """
    build_project(project_root='.', clean_product_root=clean_product_root)


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
