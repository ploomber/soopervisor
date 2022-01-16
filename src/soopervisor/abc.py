"""
Abstract classes that define the protocol for all exporters
"""
import abc
from pathlib import Path
from collections.abc import Mapping
from typing import Optional, List

import click
import yaml
from pydantic import BaseModel
from ploomber.io._commander import Commander

from soopervisor import commons


class AbstractConfig(BaseModel, abc.ABC):
    """
    Configuration schema

    Parameters
    ----------
    include : list of str
        Files/directories to include in the Docker image

    exclude : list of str
        Files/directories to exclude from the Docker image
    """
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None

    class Config:
        extra = 'forbid'

    @classmethod
    def from_file_with_root_key(cls, path_to_config, env_name):
        # write defaults, if needed
        cls._write_defaults(path_to_config, env_name)

        data = yaml.safe_load(Path(path_to_config).read_text())

        # check data is a dictionary

        # check data[env_name] is a dictionary
        if not isinstance(data[env_name], Mapping):
            raise TypeError(f'Expected {env_name!r} to be a dictionary, '
                            f'got {type(data[env_name]).__name__}')

        # check env_name in data, otherwise the env is corrupted

        if 'backend' not in data[env_name]:
            raise click.ClickException(
                'Missing backend key for '
                f'target {env_name} in {path_to_config!s}. Add it and try '
                'again.')

        actual = data[env_name]['backend']
        expected = cls.get_backend_value()

        if actual != expected:
            raise click.ClickException(
                f'Invalid backend key for target {env_name} in '
                f'{path_to_config!s}. Expected {expected!r}, actual {actual!r}'
            )

        del data[env_name]['backend']

        return cls(**data[env_name])

    @classmethod
    def _write_defaults(cls, path_to_config, env_name):
        data = cls.defaults()
        default_data = yaml.safe_dump({env_name: data})

        # if no config file, write one with env_name section and defaults
        if not Path(path_to_config).exists():
            Path(path_to_config).write_text(default_data)
        # if config file but missing env_name section, add one with defaults
        else:
            path = Path(path_to_config)
            content = path.read_text()

            if env_name not in yaml.safe_load(content):
                path.write_text(content + f'\n{default_data}\n')

    @classmethod
    @abc.abstractmethod
    def get_backend_value(cls):
        pass

    @classmethod
    def defaults(cls):
        data = dict(cls())
        data['backend'] = cls.get_backend_value()
        return data


class AbstractExporter(abc.ABC):
    """
    Steps:
    1. Initialize configuration object
    2. Perform general validation (applicable to all targets)
    3. Perfom particular validation (specific rules to the target)
    4. Run [add] step: generates files needed to export
    3. Run [submit] step: execute/deploy to the target

    Parameters
    ----------
    path_to_config : str or pathlib.Path
        Path to the configuration file

    env_name : str
        Environment name
    """
    CONFIG_CLASS = None

    def __init__(self, path_to_config, env_name):
        # ensure that the project and the config make sense
        self.validate()

        # initialize configuration and a few checks on it
        self._cfg = self.CONFIG_CLASS.from_file_with_root_key(
            path_to_config=path_to_config,
            env_name=env_name,
        )

        self._env_name = env_name

        # initialize dag (needed for validation)
        # TODO: _export also has to find_spec, maybe load it here and
        # pass it directly to _export?
        with Commander() as cmdr:
            spec, _ = commons.find_spec(cmdr=cmdr, name=env_name)

        self._dag = spec.to_dag().render(force=True, show_progress=False)

        # validate specific details about the target
        self._validate(self._cfg, self._dag, self._env_name)

    def validate(self):
        """
        Verify project has the right structure before running the script.
        This runs as a sanity check in the development machine
        """
        commons.dependencies.check_lock_files_exist()

    def add(self):
        # check that env_name folder does not exist
        path = Path(self._env_name)

        if path.exists():
            Path(self._env_name)

            kind = 'file' if path.is_file() else 'directory'
            raise FileExistsError(
                f'A {kind} with name {self._env_name!r} '
                'already exists, delete or rename it and try again')

        path.mkdir()

        return self._add(cfg=self._cfg, env_name=self._env_name)

    def export(self, mode, until=None, skip_tests=False, ignore_git=False):
        return self._export(cfg=self._cfg,
                            env_name=self._env_name,
                            mode=mode,
                            until=until,
                            skip_tests=skip_tests,
                            ignore_git=ignore_git)

    @staticmethod
    @abc.abstractmethod
    def _validate(cfg, dag, env_name):
        """Validate project before generating exported files
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def _add():
        """
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def _export(cfg, env_name, mode, until):
        pass
