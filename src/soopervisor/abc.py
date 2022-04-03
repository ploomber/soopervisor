"""
Abstract classes that define the protocol for all exporters
"""
import abc
from pathlib import Path
from collections.abc import Mapping
from typing import Optional, List
from copy import deepcopy

import yaml
from pydantic import BaseModel

from soopervisor import commons
from soopervisor.exceptions import (BackendWithoutPresetsError,
                                    InvalidPresetForBackendError,
                                    ConfigurationError)
from soopervisor._io import load_config_file
from soopervisor.commons.dag import load_dag_and_spec


class AbstractConfig(BaseModel, abc.ABC):
    """Abstract class for configuration objects

    Parameters
    ----------
    preset : str
        The preset to use, this determines certain settings and is
        backend-specific
    """
    preset: Optional[str] = None

    class Config:
        extra = 'forbid'

    @classmethod
    def load(cls, path_to_config, env_name):
        """
        Load the target environment configuration from a given YAML config
        file. Creates one if needed.
        """
        data = load_config_file(path_to_config, expected_env_name=env_name)

        # check data[env_name] is a dictionary
        if not isinstance(data[env_name], Mapping):
            raise ConfigurationError(
                f'Expected key {env_name!r} in {str(path_to_config)!r} '
                'to contain a dictionary, '
                f'got {type(data[env_name]).__name__}')

        return cls._init(env_name, data[env_name], path_to_config)

    @classmethod
    def _init(cls, env_name, data, path_to_config):
        """Initialize the Config object and perform validations

        Parameters
        ----------
        env_name
            Target environment name, only used for displaying it in errors

        data
            Dictionary used to initialize the config object

        path_to_config
            Path to the config file, only used for displaying it in errors
        """
        # check env_name in data, otherwise the env is corrupted
        data = deepcopy(data)

        if 'backend' not in data:
            raise ConfigurationError(
                f'Missing {"backend"!r} key for '
                f'section {env_name!r} in {path_to_config!r}. '
                'Add it and try again.')

        actual = data['backend']
        backend = cls.get_backend_value()

        if actual != backend:
            raise ConfigurationError(
                f'Invalid backend key for section {env_name!r} in '
                f'{path_to_config!s}. Expected {backend!r}, '
                f'actual {actual!r}')

        del data['backend']

        cfg = cls(**data)

        # validate presets is valid
        presets = cls.get_presets()

        if presets is None and cfg.preset:
            raise BackendWithoutPresetsError(backend)

        if presets:
            if cfg.preset is None:
                cfg.preset = presets[0]

            if cfg.preset not in presets:
                raise InvalidPresetForBackendError(backend, cfg.preset,
                                                   presets)

        return cfg

    @classmethod
    def new(cls, path_to_config, env_name, preset=None, **defaults):
        """
        Validates, then writes a configuration setting in the selected file

        Parameters
        ----------
        path_to_config
            Path to the config file

        env_name
            Target environment

        preset
            Target environment preset

        defaults
            Any other values to store
        """
        if Path(env_name).exists():
            type_ = 'directory' if Path(env_name).is_dir() else 'file'
            raise ConfigurationError(
                f'A {type_} named '
                f'{env_name!r} already exists in the current working '
                'directory, select another name for the target environment'
                ' and try again.')

        data = {**cls.hints(), **defaults}

        if preset:
            data['preset'] = preset

        # initialize config before storing the yaml to halt execution
        # in case there are any validation errors
        cfg = cls._init(env_name, data, path_to_config)

        # pass default_flow_style=None to it serializes lists as [a, b, c]
        default_data = yaml.safe_dump({env_name: data},
                                      default_flow_style=None)

        # if no config file, write one with env_name section and hints
        if not Path(path_to_config).exists():
            Path(path_to_config).write_text(default_data)

        # if config file but missing env_name section, add one with the hints
        else:
            path = Path(path_to_config)
            content = path.read_text()
            env_names = list(load_config_file(path_to_config))

            # only update the config file if the section does not exist
            if env_name not in env_names:
                # append to the text file so we don't delete any existing
                # comments
                path.write_text(content + f'\n{default_data}\n')
            else:
                raise ConfigurationError(
                    'A target environment named '
                    f'{env_name!r} already exists in {str(path_to_config)!r}, '
                    'select another name and try again.')

        return cfg

    @classmethod
    @abc.abstractmethod
    def get_backend_value(cls):
        """Returns the string identifier for the given backend
        """
        pass

    @classmethod
    def get_presets(cls):
        return None

    @classmethod
    def _hints(cls):
        """
        Hints must return a dictionary with descriptive values that help
        the user understand what each field means. They are not necessarilly
        values that work. For example, in docker-based exporters, the
        user needs to specify a repository. So we have a hint of
        your-repository/name (this is what the user sees when they create the
        target environment). This contrasts with default values (declared
        in the pydantic model). Default values are *acceptable values*,
        but are not necessarily descriptive. For example, the default value
        for repository is None, meaning there is not remote repository.
        """
        return {}

    @classmethod
    def hints(cls):
        """
        Returns a dictiionary with the values to use when a target environment
        is created, it also adds the appropriate backend value. Actual
        hint values must be returned in the _hints() method
        """
        data = cls._hints()
        data['backend'] = cls.get_backend_value()
        return data


class AbstractDockerConfig(AbstractConfig):
    """
    An abstract class for docker-based configurations where having a remote
    repository is optional (e.g., can build an image locally)

    include : list of str
        Files/directories to include in the Docker image

    exclude : list of str
        Files/directories to exclude from the Docker image
    """
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    repository: Optional[str] = None

    @classmethod
    def _hints(cls):
        return dict(repository='your-repository/name')


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

    preset : str, default=None
        The backend preset (customizes the configuration). If this isn't
        None and the concrete class does not take a present, it will raise
        an exception
    """
    CONFIG_CLASS = None

    def __init__(self, cfg, dag, env_name):
        # initialize configuration, write to config file and a few checks on
        # it
        self._cfg = cfg
        self._env_name = env_name
        self._dag = dag

        # check backend-specific rrules
        self._validate(self._cfg, self._dag, self._env_name)

    @classmethod
    def load(cls, path_to_config, env_name, lazy_import=False):
        """
        Loads an exporter using settings from an existing configuration file
        """
        # run some basic validations
        cls.validate()

        dag, _ = load_dag_and_spec(env_name, lazy_import=lazy_import)

        cfg = cls.CONFIG_CLASS.load(path_to_config=path_to_config,
                                    env_name=env_name)

        return cls(cfg, dag, env_name)

    @classmethod
    def new(cls, path_to_config, env_name, preset=None, lazy_import=False):
        """
        """
        # run some basic validations
        cls.validate()

        dag, spec = load_dag_and_spec(env_name, lazy_import=lazy_import)

        if issubclass(cls.CONFIG_CLASS, AbstractDockerConfig):
            # it the spec has products store in relative paths, get them and
            # exclude them
            prod_prefix = commons.product_prefixes_from_spec(spec)
            defaults = {} if not prod_prefix else dict(exclude=prod_prefix)
        else:
            defaults = {}

        cfg = cls.CONFIG_CLASS.new(
            path_to_config=path_to_config,
            env_name=env_name,
            preset=preset,
            **defaults,
        )

        return cls(cfg, dag, env_name)

    @classmethod
    def validate(cls):
        """
        Verify project has the right structure before running the script.
        This runs as a sanity check in the development machine
        """
        commons.dependencies.check_lock_files_exist()

    def add(self):
        """Create a directory with the env_name and add any necessary files
        """

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

    def export(self,
               mode,
               until=None,
               skip_tests=False,
               ignore_git=False,
               lazy_import=False):
        """
        Exports to the target environment, calls the private ._export()
        method
        """
        # TODO: detect inconsistencies. e.g., environment exists but directory
        # doesnt
        return self._export(cfg=self._cfg,
                            env_name=self._env_name,
                            mode=mode,
                            until=until,
                            skip_tests=skip_tests,
                            ignore_git=ignore_git,
                            lazy_import=lazy_import)

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
        Private method implementing the backend-specific logic for the add
        command
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def _export(cfg, env_name, mode, until):
        """
        Private method implementing the backend-specific logic for the export
        command
        """
        pass
