import click
from pathlib import Path

import yaml

from soopervisor.enum import Backend
from soopervisor import validate, exceptions
from soopervisor._format import comma_separated


def get_backend(name):
    """
    Loads soopervisor.yaml and loads the configuration for an env with the
    passed name. Performs validations before returning the configuration
    """
    validate.config_file_exists()

    # load soopervisor.yaml
    cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())

    # get section with that name
    if name not in cfg:
        raise exceptions.ConfigurationError(
            f'Missing {name!r} section in {"soopervisor.yaml"!r}. '
            f'Available ones are: {comma_separated(cfg)}')

    section = cfg[name]

    # check if there is a backend key
    if 'backend' not in section:
        raise exceptions.ConfigurationError(
            'Misconfigured environment: missing '
            f'\'backend\' key in section {name!r} in '
            '\'soopervisor.yaml\'')

    backend = section['backend']

    # check if the value is valid
    if backend not in Backend:
        valid = comma_separated(Backend.__members__.keys())
        raise exceptions.ConfigurationError(
            f'Misconfigured environment: {backend!r} is '
            f'not a valid backend. backend must be one of: {valid}')

    return backend


def replace_env(env_name, target_dir):
    """
    For a given target directory, renames env.{env_name}.yaml to env.yaml
    """
    env = Path(target_dir, f'env.{env_name}.yaml')

    if env.exists():
        env_general = Path(target_dir, 'env.yaml')

        if env_general.exists():
            env_general.unlink()
        else:
            click.echo(f'No {env} found...')

        env.rename(env_general)
