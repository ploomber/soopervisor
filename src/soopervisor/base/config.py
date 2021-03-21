"""
Configuration objects declare the schema for the configuration file, perform
schema validation, compute some attributes dynamically and render placeholders
"""
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import validator, Field
from jinja2 import Template, meta
import yaml

from ploomber.util import default
from soopervisor.script.script import generate_script
from soopervisor.git_handler import GitRepo
from soopervisor.base import validate as validate_base
from soopervisor.base.abstract import AbstractBaseModel, AbstractConfig


class StorageConfig(AbstractBaseModel):
    """Store pipeline products after execution

    Parameters
    ----------
    provider : str, default=None
        'box' for uploading files to box or 'local' to just copy files
        to a local directory. None to disable

    path : str, default='runs/{{now}}'
        Path where the files will be moved, defaults to runs/{{now}},
        where {{now}} will be replaced by the current timestamp in ISO 8601
        format. {{git}} is also available, it's replaced by the current git
        hash, requires the project to be in a git repository.

    credentials : str, default=None
        Credentials for the storage provider, only required if provider
        is not 'local'
    """
    provider: Optional[str] = None
    path: Optional[str] = 'runs/{{now}}'
    credentials: Optional[str] = None

    # this is not a field, but a reference to the paths section
    paths: Optional[str]

    def __init__(self, *, paths, **data) -> None:
        super().__init__(**data)
        self.paths = paths
        self.render()

    @validator('provider', always=True)
    def validate_provider(cls, v):
        valid = {'box', 'local', None}
        if v not in valid:
            raise ValueError(f'Provider must be one of: {valid}')
        return v

    def render(self):
        # only expand if storage is enabled
        if self.provider:
            template = Template(self.path)
            env = template.environment
            vars_ = meta.find_undeclared_variables(env.parse(self.path))
            available = {'git', 'now'}
            extra = vars_ - available

            if extra:
                raise ValueError(f'Got unrecognized placeholders: {extra}')

            to_pass = {}

            if 'git' in vars_:
                to_pass['git'] = GitRepo(self.paths.project).get_git_hash()

            if 'now' in vars_:
                to_pass['now'] = datetime.now().isoformat(timespec='seconds')

            self.path = template.render(**to_pass)

            # TODO: we should do some validation here, to prevent raising
            # errors at runtime


class Paths(AbstractBaseModel):
    """Project's paths

    Parameters
    ----------
    project : str, default='.'
        Project's root folder

    products : str, default='output'
        Project product's root. Anything inside this folder is considered
        a  product upon pipeline execution. If relative, it is so to the
        project's root, not to the current working directory. Every file on
        this folder will be uploaded if "storage" is configured.

    environment : str, default='environment.yml'
        Path to conda environment YAML spec. A virtual environment is created
        using this file before executing the pipeline. If relative, it is so to
        the project's root, not to the current working directory.
    """
    project: Optional[str] = '.'
    # this only used by storage, maybe move to Storage then.
    # although we need it for airflow when running in docker/kubernetes
    # because we need to make sure all products will be generated in a
    # single folder so we know what to mount - we have to think this,
    # cause there is some overlap but in the end, exporting is a different
    # operation than product storage
    # NOTE: support for a glob pattern would be useful
    products: Optional[str] = 'output'
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
        self.products = self._resolve_path(self.products)

    def _resolve_path(self, path):
        if Path(path).is_absolute():
            return str(Path(path).resolve())
        else:
            return str(Path(self.project, path).resolve())

    def __str__(self):
        return ('Paths:'
                f'\n  * Project root: {self.project}'
                f'\n  * Products: {self.products}'
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

    storage : dict
        Section to configure product's upload after execution, see
        StorageConfig for schema

    lazy_import : bool, default=False
        When processing your project, the DAG is initialized to run a few
        validations on it. If your pipeline has any dotted paths
        (e.g. tasks that are Python functions), they will be imported by
        default, if this option is False, they will not be imported. This
        limits the number of validation checks but allows you to process your
        pipeline without having to setup an environment that has all
        dependencies required to import dotted paths
    """
    # NOTE: should args be "--force" by defauult, when using soopervisor,
    # we are in production mode so it doesn't make sense to do incremental
    # builds
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
    storage: StorageConfig = None

    # COMPUTED FIELDS
    environment_name: Optional[str] = None

    def __init__(self, **data) -> None:
        if 'storage' in data:
            storage = data.pop('storage')
        else:
            storage = {}

        super().__init__(**data)
        self.storage = StorageConfig(paths=self.paths, **storage)
        self.render()

    @classmethod
    # FIXME: remove parameters we are no longer using
    def from_project(cls,
                     project_root,
                     validate=True,
                     return_dag=False,
                     load_dag=True):
        """
        Initializes a ScriptConfig from a project. Looks for a
        project/soopervisor.yaml file, if it doesn't exist, it just
        initializes with default values, except by paths.project, which is set
        to ``project``

        Parameters
        ----------
        project_root : str or pathlib.Path
            The project's location
        """
        path = Path(project_root, 'soopervisor.yaml')

        if path.exists():
            with open(str(path)) as f:
                d = yaml.safe_load(f)

            # allow initialization with empty file
            if d is None:
                d = dict()

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

        if validate:
            dag = validate_base.project(config, load_dag=load_dag)
        else:
            dag = None

        return config if not return_dag else (config, dag)

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

    # TODO: remove, config objects should not implement this logic
    def clean_products(self):
        if Path(self.paths.products).exists():
            shutil.rmtree(self.paths.products)
            Path(self.paths.products).mkdir()

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
        d_storage = dict(d['storage'])
        del d_storage['paths']

        d['paths'] = d_path
        d['storage'] = d_storage

        root_old = d['paths']['project']

        d['paths']['project'] = project_root
        d['paths']['products'] = d['paths']['products'].replace(
            root_old, project_root)
        d['paths']['environment'] = d['paths']['environment'].replace(
            root_old, project_root)

        return type(self)(**d)
