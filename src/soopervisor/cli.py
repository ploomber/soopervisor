from pathlib import Path
import yaml
import click

from soopervisor import __version__
from soopervisor import config
from soopervisor import exporter
from soopervisor.enum import Backend, Mode
from ploomber.telemetry import telemetry


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Soopervisor exports Ploomber projects.

    Example (export to Argo Workflows for training):

    $ soopervisor add training --backend argo-workflows

    $ soopervisor export training

    """
    pass


@cli.command()
@click.argument('env_name')
@click.option('--backend',
              '-b',
              type=click.Choice(Backend.get_values()),
              required=True)
def add(env_name, backend):
    """Add a new target platform
    """
    backend = Backend(backend)
    try:
        if Path('soopervisor.yaml').exists():
            cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())
            if env_name in cfg:
                raise click.ClickException(
                    f'A {env_name!r} section in the '
                    'soopervisor.yaml configuration file '
                    'already exists. Choose another name.')
        if Path(env_name).exists():
            raise click.ClickException(
                f'{env_name!r} already exists. Select a different name.')
    except Exception as e:
        telemetry.log_api("soopervisor_export_error",
                          metadata={
                              'type': backend,
                              'env_name': env_name,
                              'error': e
                          })
        raise

    Exporter = exporter.for_backend(backend)
    Exporter('soopervisor.yaml', env_name=env_name).add()
    telemetry.log_api("soopervisor_add_success",
                      metadata={
                          'type': backend,
                          'env_name': env_name
                      })


@cli.command()
@click.argument('env_name')
@click.option('--until-build',
              '-u',
              is_flag=True,
              help='Only build docker image')
@click.option('--skip-tests',
              '-s',
              is_flag=True,
              help='Skip docker image tests')
@click.option('--mode',
              '-m',
              type=click.Choice(Mode.get_values()),
              default=Mode.incremental.value)
@click.option('--ignore-git',
              '-i',
              is_flag=True,
              help='Ignore git tracked files (include everything)')
def export(env_name, until_build, mode, skip_tests, ignore_git):
    """
    Export a target platform for execution/deployment
    """
    input_args = {
        'env_name': env_name,
        'until_build': until_build,
        'mode': mode,
        'skip_tests': skip_tests,
        'ignore_git': ignore_git
    }
    try:
        backend = Backend(config.get_backend(env_name))

        telemetry.log_api("soopervisor_export_started",
                          metadata={
                              'type': backend,
                              'input_args': input_args
                          })

        until = None

        if until_build:
            until = 'build'

        # TODO: ignore mode if using aws lambda, raised exception if value
        # is not the default
        if backend == Backend.aws_lambda:
            mode = None

        Exporter = exporter.for_backend(backend)

        Exporter('soopervisor.yaml',
                 env_name=env_name).export(mode=mode,
                                           until=until,
                                           skip_tests=skip_tests,
                                           ignore_git=ignore_git)
        telemetry.log_api("soopervisor_export_success",
                          metadata={
                              'type': backend,
                              'input_args': input_args
                          })
    except Exception as e:
        telemetry.log_api("soopervisor_export_error",
                          metadata={
                              'type': backend,
                              'input_args': input_args,
                              'error': e
                          })
        raise


if __name__ == '__main__':
    cli()
