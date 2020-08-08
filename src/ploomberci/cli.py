import click

from ploomberci import build


@click.command()
def cli():
    """
    Execute project
    """
    build.build_project('.')


if __name__ == '__main__':
    cli()
