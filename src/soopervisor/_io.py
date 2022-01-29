from collections.abc import Mapping
from pathlib import Path

import yaml

from soopervisor.exceptions import (ConfigurationFileTypeError,
                                    ConfigurationError)


def load_config_file(path='soopervisor.yaml', expected_env_name=None):
    """
    Load a config file, validates that the returned value is a dictionary,
    optionally validates the existence of certain key
    """
    path = Path(path)

    if not path.exists():
        raise ConfigurationError(f'Error loading {str(path)!r}. File '
                                 'does not exist.')

    if path.is_dir():
        raise ConfigurationError(f'Error loading {str(path)!r}. Path '
                                 'is a directory.')

    data = yaml.safe_load(Path(path).read_text())

    if not isinstance(data, Mapping):
        raise ConfigurationFileTypeError(path, data)

    if expected_env_name and expected_env_name not in data:
        raise ConfigurationError(f'{str(path)!r} does not contain a target '
                                 f'environment named {expected_env_name!r}')

    return data
