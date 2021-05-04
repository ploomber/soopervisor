from pathlib import Path

import yaml

from soopervisor.enum import Backend
from soopervisor.exceptions import ConfigurationError


def get_backend(name):
    cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())

    if name not in cfg:
        raise ConfigurationError('Misconfigured environment: missing '
                                 f'{name!r} section in soopervisor.yaml')

    section = cfg[name]

    if 'backend' not in section:
        raise ConfigurationError('Misconfigured environment: missing '
                                 f'\'backend\' key in section {name!r} in '
                                 'soopervisor.yaml')

    backend = section['backend']

    if backend not in Backend:
        valid = list(Backend.__members__.keys())
        raise ConfigurationError(
            f'Misconfigured environment: {backend!r} is '
            f'not a valid backend. backend must be one of: {valid}')

    return backend
