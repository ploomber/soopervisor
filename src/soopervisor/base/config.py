"""
Configuration objects declare the schema for the configuration file, perform
schema validation, compute some attributes dynamically and render placeholders
"""
from pathlib import Path
from typing import Optional

from pydantic import validator, Field
import yaml

from ploomber.util import default
from soopervisor.script.script import generate_script
from soopervisor.base.abstract import AbstractBaseModel, AbstractConfig


class Paths(AbstractBaseModel):
    """Project's paths

    Parameters
    ----------
    project : str, default='.'
        Project's root folder

    environment : str, default='environment.yml'
        Path to conda environment YAML spec. A virtual environment is created
        using this file before executing the pipeline. If relative, it is so to
        the project's root, not to the current working directory.
    """
    project: Optional[str] = '.'
    environment: Optional[str] = 'environment.yml'

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # maybe call this in the super class?
        self.render()

    @validator('project', always=True)
    def project_must_be_absolute(cls, v):
        return str(Path(v).resolve())

    @property
    def entry_point(self):
        """
        Returns a path to the entry point by looking in standard locations
        (uses Ploomber's API)
        """
        # this returns the default location relative to self.project
        entry_point = default.entry_point(self.project)
        return Path(self.project, entry_point)

    def render(self):
        self.environment = self._resolve_path(self.environment)

    def _resolve_path(self, path):
        if Path(path).is_absolute():
            return str(Path(path).resolve())
        else:
            return str(Path(self.project, path).resolve())

    def __str__(self):
        return ('Paths:'
                f'\n  * Project root: {self.project}'
                f'\n  * Environment: {self.environment}')


class ScriptConfig(AbstractConfig):
    """Configuration schema to execute Ploomber pipelines

    Parameters
    ----------
    cache_env : bool, default=False
        If True, re-use conda virtual environment if it exists, otherwise, it
        creates it every time the pipeline runs

    executor : {'local', 'docker'}, default='local'
        If 'local', the pipeline executes in a subprocess, if 'docker', it is
        executed using a Docker container (for this to work, Docker must be
        already configured and ready to use)

    environment_prefix : str, default=None
        If None, the conda virtual environment is created in the standard
        location (usually ``~/miniconda/envs/{env-name}``), otherwise it is
        created is a custom location. If relative, it is so to project's root,
        not to the current working directory.

    allow_incremental : bool, default=True
        Allow pipeline execution with non-empty product folders

    args : str, default=''
        Extra cli arguments to pass when executing the pipeline

    paths : dict
        Section to configure project paths, see Paths for schema

    lazy_import : bool, default=False
        When processing your project, the DAG is initialized to run a few
        validations on it. If your pipeline has any dotted paths
        (e.g. tasks that are Python functions), they will be imported by
        default, if this option is False, they will not be imported. This
        limits the number of validation checks but allows you to process your
        pipeline without having to setup an environment that has all
        dependencies required to import dotted paths
    """
    # TODO: Create env again only if environment.yml has changed
    cache_env: Optional[bool] = False
    executor: Optional[str] = 'local'
    environment_prefix: Optional[str] = None
    allow_incremental: Optional[bool] = True
    args: Optional[str] = ''
    # TODO: make this and load_dag the same option, maybe:
    # validate_dag: True, False or 'lazy'
    lazy_import: bool = False

    # sub sections
    paths: Optional[Paths] = Field(default_factory=Paths)

    # COMPUTED FIELDS
    environment_name: Optional[str] = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.render()

    @classmethod
    def from_file_with_root_key(cls, path_to_config, env_name):
        """
        Initializes a ScriptConfig from a project. Looks for a
        soopervisor.yaml file, if it doesn't exist, it just
        initializes with default values
        """
        path = Path(path_to_config)
        project_root = path.parent.resolve()

        if path.exists():
            with open(str(path)) as f:
                d = yaml.safe_load(f)

            # make this logic common across backends
            # maybe raise an error if the key doesn't exist?
            # only allow it to be empty when creating the env
            if env_name not in d:
                # TODO: create content based on some defaults
                original = Path(path).read_text()
                Path(path).write_text(original + '\n' + f'{env_name}: null\n')
                d = dict()
            else:
                d = d[env_name] or dict()

            # TODO: validate d is a dictionary, if empty, yaml.safe_load
            # returns None, and it can also returns lists

            if 'paths' in d and 'project' in d['paths']:
                proj = d['paths']['project']
                if Path(proj).is_absolute():
                    raise ValueError(
                        'Relative paths in paths.project are not '
                        'allowed when initializing a project '
                        'that is not in the current working directory. '
                        f'Edit paths.project in {path} and change the '
                        f'current value ({proj!r}) to a relative path')

            if 'paths' not in d:
                d['paths'] = dict()

            d['paths']['project'] = str(project_root)
            config = cls(**d)
        else:
            config = cls(paths=dict(project=str(project_root)))

        return config

    # TODO: remove, config objects should not implement this logic
    def to_script(self, command=None):
        return generate_script(config=self, command=command)

    def render(self):
        if self.environment_prefix is not None:
            self.environment_prefix = self._resolve_path(
                self.environment_prefix)
            self.environment_name = self.environment_prefix
        else:
            if Path(self.paths.environment).exists():
                with open(self.paths.environment) as f:
                    env_spec = yaml.safe_load(f)

                try:
                    self.environment_name = env_spec['name']
                except Exception:
                    pass

        return self

    def _resolve_path(self, path):
        if Path(path).is_absolute():
            return str(Path(path).resolve())
        else:
            return str(Path(self.paths.project, path).resolve())

    # TODO: remove, config objects should not implement this logic
    def save_script(self):
        """
        Generate, validate and save script to the project's root directory,
        returns script location
        """
        script = self.to_script()
        path_to_script = Path(self.paths.project, 'script.sh')
        path_to_script.write_text(script)
        return str(path_to_script)

    # TODO: make this a computed field
    @property
    def project_name(self):
        return str(Path(self.paths.project).resolve().name)

    def with_project_root(self, project_root):
        """
        Generate a new instance with the same value but a new project root,
        currently used to generate the Argo YAML spec, the spec is generated
        by analyzing the current DAG locally but it must contain the product
        root when executed in the cluster
        """
        project_root = str(Path(project_root).resolve())

        d = dict(self)
        d_path = dict(d['paths'])

        d['paths'] = d_path

        root_old = d['paths']['project']

        d['paths']['project'] = project_root
        d['paths']['environment'] = d['paths']['environment'].replace(
            root_old, project_root)

        return type(self)(**d)
