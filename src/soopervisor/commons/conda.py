from click import ClickException
from collections.abc import Mapping
from pathlib import Path

import yaml


def extract_pip_from_env_yaml(path):
    env = yaml.safe_load(Path(path).read_text())

    if 'dependencies' not in env:
        raise ClickException(
            'Cannot extract pip dependencies from '
            'environment.lock.yml: missing dependencies section')

    deps = env['dependencies']

    for dep in deps:
        if isinstance(dep, Mapping):
            if 'pip' in dep:
                deps_pip = dep['pip']

                if not isinstance(deps_pip, list):
                    raise ClickException(
                        'Cannot extract pip dependencies '
                        'from environment.lock.yml: unexpected '
                        'dependencies.pip value. Expected a '
                        f'list of dependencies, got: {deps_pip}')

                return deps_pip

    raise ClickException(
        'Cannot extract pip dependencies from '
        'environment.lock.yml: missing dependencies.pip section')


def generate_reqs_txt_from_env_yml(path, output):
    reqs = extract_pip_from_env_yaml(path)
    Path(output).write_text('\n'.join(reqs))
