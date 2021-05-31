import importlib
from pathlib import Path

from click import ClickException
from ploomber.util import default
from ploomber.io._commander import CommanderStop
from soopervisor.commons import source


def build(e, cfg, name, until, skip_tests=False):
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

    skip_tests : bool, default=False
        Skip image testing (check dag loading and File.client configuration)
    """

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

    if Path('requirements.lock.txt').exists():
        e.cp('requirements.lock.txt')
    elif Path('environment.lock.yml').exists():
        e.cp('environment.lock.yml')
    else:
        raise ClickException('Expected environment.lock.yml or '
                             'requirements.txt.lock at the root '
                             'directory. Add one and try again')

    # generate source distribution

    if Path('setup.py').exists():
        # .egg-info may cause issues if MANIFEST.in was recently updated
        e.rm('dist', 'build', Path('src', pkg_name, f'{pkg_name}.egg-info'))
        e.run('python', '-m', 'build', '--sdist', description='Packaging code')

        # raise error if include is not None? use MANIFEST.instead
    else:
        # TODO: warn on unsaved changes (new files will not be included
        # since they are not yet tracked on git)
        e.rm('dist')
        target = Path('dist', pkg_name)
        e.info('Packaging code')
        source.copy('.', target, include=cfg.include)
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
              description='Testing image',
              error_message='Error while testing your docker image with',
              hint=f'Use "docker run -it {image_local} /bin/bash" to '
              'start an interactive session to debug your image')

        # check that the pipeline in the image has a configured File.client
        test_cmd = ('from ploomber.spec import DAGSpec; '
                    'print("File" in DAGSpec.find().to_dag().clients)')
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

    # TODO: validate format of cfg.repository
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
