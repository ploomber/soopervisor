import importlib
from pathlib import Path

from ploomber.util import default
from ploomber.io._commander import CommanderStop


def build(e, cfg, name, until):
    pkg_name = default.find_package_name()
    # if using versioneer, the version may contain "+"
    version = importlib.import_module(pkg_name).__version__.replace(
        '+', '-plus-')

    e.cp('environment.lock.yml')

    # generate source distribution

    # .egg-info may cause issues if MANIFEST.in was recently updated
    e.rm('dist', 'build', Path('src', pkg_name, f'{pkg_name}.egg-info'))
    e.run('python', '-m', 'build', '--sdist', description='Packaging code')
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

    e.run('docker',
          'run',
          image_local,
          'ploomber',
          'status',
          description='Testing image',
          error_message='Error while testing your docker image with',
          hint=f'Use "docker run -it {image_local} /bin/bash" to '
          'start an interactive session to debug your image')

    test_cmd = ('from ploomber.spec import DAGSpec; '
                'print("File" in DAGSpec.find().to_dag().clients)')
    e.run('docker',
          'run',
          image_local,
          'python',
          '-c',
          test_cmd,
          description='Testing image',
          error_message='Error while checking File client configuration',
          hint=f'Use "docker run -it {image_local} /bin/bash" to '
          'start an interactive session to debug your image and ensure a '
          'File client is properly configured',
          capture_output=True,
          expected_output='True\n')

    if until == 'build':
        raise CommanderStop('Done. Run "docker images" to see your image.')

    # TODO: validate format of cfg.submit.repository
    if cfg.submit.repository:
        image_target = f'{cfg.submit.repository}:{version}'
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
