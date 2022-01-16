import importlib
from pathlib import Path

from ploomber.util import default
from ploomber.io._commander import CommanderStop

from soopervisor.commons import source, dependencies
from soopervisor.exceptions import ConfigurationError


def _validate_repository(repository):
    if repository == 'your-repository/name':
        raise ConfigurationError(
            f'Invalid repository {repository!r} '
            'in soopervisor.yaml, please add a valid value.')


def build(e,
          cfg,
          name,
          until,
          entry_point,
          skip_tests=False,
          ignore_git=False):
    """Build a docker image

    Parameters
    ----------
    e : Commander
        Commander instance

    cfg
        Configuration

    name : str
        Target environment name

    until : str
        Stop after certain starge

    entry_point : str
        Entry point to use path/to/pipeline.yaml

    skip_tests : bool, default=False
        Skip image testing (check dag loading and File.client configuration)
    """
    # raise an error if the user didn't change the default value
    _validate_repository(cfg.repository)

    # if this is a pkg, get the name
    try:
        pkg_name = default.find_package_name()
    # if not a package, use the parent folder's name
    except ValueError:
        pkg_name = Path('.').resolve().name
        version = 'latest'
    else:
        # if using versioneer, the version may contain "+"
        version = importlib.import_module(pkg_name).__version__.replace(
            '+', '-plus-')

    dependencies.check_lock_files_exist()

    if Path('requirements.lock.txt').exists():
        e.cp('requirements.lock.txt')
    elif Path('environment.lock.yml').exists():
        e.cp('environment.lock.yml')

    # generate source distribution

    if Path('setup.py').exists():
        # .egg-info may cause issues if MANIFEST.in was recently updated
        e.rm('dist', 'build', Path('src', pkg_name, f'{pkg_name}.egg-info'))
        e.run('python', '-m', 'build', '--sdist', description='Packaging code')

        # raise error if include is not None? and suggest to use MANIFEST.in
        # instead
    else:
        e.rm('dist')
        target = Path('dist', pkg_name)
        e.info('Packaging code')
        source.copy(cmdr=e,
                    src='.',
                    dst=target,
                    include=cfg.include,
                    exclude=cfg.exclude,
                    ignore_git=ignore_git)
        source.compress_dir(target, Path('dist', f'{pkg_name}.tar.gz'))

    e.cp('dist')

    e.cd(name)

    image_local = f'{pkg_name}:{version}'

    # how to allow passing --no-cache?
    e.run('docker',
          'build',
          '.',
          '--tag',
          image_local,
          description='Building image')

    if not skip_tests:
        # test "ploomber status" in docker image
        e.run('docker',
              'run',
              image_local,
              'ploomber',
              'status',
              '--entry-point',
              entry_point,
              description='Testing image',
              error_message='Error while testing your docker image with',
              hint=f'Use "docker run -it {image_local} /bin/bash" to '
              'start an interactive session to debug your image')

        # check that the pipeline in the image has a configured File.client
        test_cmd = ('from ploomber.spec import DAGSpec; '
                    f'print("File" in DAGSpec("{entry_point}")'
                    '.to_dag().clients)')

        e.run('docker',
              'run',
              image_local,
              'python',
              '-c',
              test_cmd,
              description='Testing File client',
              error_message='Missing File client',
              hint=f'Run "docker run -it {image_local} /bin/bash" to '
              'to debug your image. Ensure a File client is configured',
              capture_output=True,
              expected_output='True\n',
              show_cmd=False)

    if until == 'build':
        raise CommanderStop('Done. Run "docker images" to see your image.')

    if cfg.repository:
        image_target = f'{cfg.repository}:{version}'
        e.run('docker',
              'tag',
              image_local,
              image_target,
              description='Tagging')
        e.run('docker', 'push', image_target, description='Pushing image')
    else:
        image_target = image_local

    if until == 'push':
        raise CommanderStop('Done. Image pushed to repository.')

    return pkg_name, image_target
