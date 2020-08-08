import click

import ploomberci


@click.group()
def cli(clean_product_root):
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
    ploomberci.build.build_project(project_root='.',
                                   clean_product_root=clean_product_root)


@cli.command()
def upload():
    """
    Upload files
    """
    pass


if __name__ == '__main__':
    cli()
