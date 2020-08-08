import click

from ploomberci import build


@click.command()
@click.option('--clean-product-root',
              is_flag=True,
              help='Remove all files from product_root before building')
def cli(clean_product_root):
    """
    Execute project
    """
    build.build_project(project_root='.',
                        clean_product_root=clean_product_root)


if __name__ == '__main__':
    cli()
