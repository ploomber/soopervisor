"""
Schema
------

paths:
    # path to project directory
    project: .
    # path to products directory (if relative, it is to paths.project),
    # any generated file in this folder is considered a pipeline product
    products: output/
    # path conda environment file (if relative, it is to paths.project)
    environment: environment.yml

"""
import shutil
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator, Field
from jinja2 import Template
import yaml

from soopervisor.script.script import generate_script
from soopervisor.git_handler import GitRepo
from soopervisor.storage.LocalStorage import LocalStorage
from soopervisor import validate as validate_module


class StorageConfig(BaseModel):
    """
    This section configures there to copy pipeline products after execution

    provider: str
        'box' for uploading files to box or 'local' to just copy files
        to a local directory. None to disable

    path: str
        Path where the files will be moved, defaults to runs/{{git}},
        where {{git}} will be replaced by the current git hash
    """
    paths: Optional[str]

    provider: Optional[str] = None
    path: Optional[str] = 'runs/{{git}}'
    credentials: Optional[str]

    class Config:
        extra = 'forbid'

    def __init__(self, *, paths, **data) -> None:
        super().__init__(**data)
        self.paths = paths

    @validator('provider', always=True)
    def validate_provider(cls, v):
        valid = {'box', 'local', None}
        if v not in valid:
            raise ValueError(f'Provider must be one of: {valid}')
        return v

    def check(self):
        LocalStorage(self.path)

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)

        # only expand if storage is enabled
        if d['provider']:
            d['path'] = Template(d['path']).render(
                git=GitRepo(self.paths.project).get_git_hash())

        return d


class Paths(BaseModel):
    class Config:
        validate_assignment = True
        extra = 'forbid'

    project: Optional[str] = '.'
    # this only used by storage, maybe move to Storage then.
    # although we need it for airflow when running in docker/kubernetes
    # because we need to make sure all products will be generated in a
    # single folder so we know what to mount - we have to think this,
    # cause there is some overlap but in the end, exporting is a different
    # operation than product storage
    products: Optional[str] = 'output'
    environment: Optional[str] = 'environment.yml'

    def __init__(self, **data) -> None:
        super().__init__(**data)

    @validator('project', always=True)
    def project_must_be_absolute(cls, v):
        return str(Path(v).resolve())

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        d['environment'] = self._resolve_path(d['environment'])
        d['products'] = self._resolve_path(d['products'])
        return d

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


class ScriptConfig(BaseModel):
    """
    Root section for the configuration file

    Parameters
    ----------
    paths : dict
        Section to configure important project paths

    cache_env : bool
        Create env again only if environment.yml has changed

    executor : str
        Which executor to use "local" or "docker"

    allow_incremental : bool
        If True, allows execution on non-empty product folders
    """
    # FIXME: defaults should favor convenience (less chance of errors)
    # vs speed. set cache_env to false
    paths: Optional[Paths] = Field(default_factory=Paths)
    cache_env: Optional[bool] = True
    args: Optional[str] = ''
    storage: StorageConfig = None
    executor: Optional[str] = 'local'
    allow_incremental: Optional[bool] = True
    environment_prefix: Optional[str] = None

    # TODO: add a lazy_import option? there are cases when we want to
    # instantiate the dag and render without actually executing it,
    # for rendering, we don't have to import all dotted paths (although this
    # limits our ability to do render-time checks), the benefit is that
    # we could export dags in environments that do not necessarily have
    # all dependencies installed, but just limit themselves to do a few checks
    # this is a must when loading the dag in the airflow host but could be
    # optional when exporting

    class Config:
        extra = 'forbid'

    def __init__(self, **data) -> None:
        if 'storage' in data:
            storage = data.pop('storage')
        else:
            storage = {}

        super().__init__(**data)
        self.storage = StorageConfig(paths=self.paths, **storage)
        self.storage.check()

    @classmethod
    def from_path(cls, project):
        """
        Initializes a ScriptConfig from a directory. Looks for a
        project/soopervisor.yaml file, if it doesn't exist, it just
        initializes with default values, except by paths.project, which is set
        to ``project``

        Parameters
        ----------
        project : str or pathlib.Path
            The project's location
        """
        path = Path(project, 'soopervisor.yaml')

        if path.exists():
            with open(str(path)) as f:
                d = yaml.safe_load(f)

            config = cls(**d)

        else:
            config = cls(paths=dict(project=str(project)))

        return config

    def to_script(self, validate=True, command=None):
        return generate_script(config=self.export(validate=validate),
                               command=command)

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)

        if d['environment_prefix'] is not None:
            d['environment_prefix'] = self._resolve_path(
                d['environment_prefix'])
            d['environment_name'] = d['environment_prefix']
        else:
            if Path(d['paths']['environment']).exists():
                with open(d['paths']['environment']) as f:
                    env_spec = yaml.safe_load(f)

                try:
                    d['environment_name'] = env_spec['name']
                except Exception:
                    d['environment_name'] = None
            else:
                d['environment_name'] = None

        return d

    def validate(self):
        d = self.dict()
        validate_module.project(d)

    def export(self, validate=True, return_dag=False):
        d = self.dict()

        if validate:
            dag = validate_module.project(d)
        else:
            dag = None

        return d if not return_dag else (d, dag)

    def _resolve_path(self, path):
        if Path(path).is_absolute():
            return str(Path(path).resolve())
        else:
            return str(Path(self.paths.project, path).resolve())

    def save_script(self):
        """
        Generate, validate and save script to the project's root directory,
        returns script location
        """
        script = self.to_script(validate=True)
        path_to_script = Path(self.paths.project, 'script.sh')
        path_to_script.write_text(script)
        return str(path_to_script)

    def clean_products(self):
        if Path(self.paths.products).exists():
            shutil.rmtree(self.paths.products)
            Path(self.paths.products).mkdir()


class AirflowConfig(ScriptConfig):
    """
    Configuration for exporting Ploomber (Soopervisor-compliant) projects to
    Airflow. Same schema as ScriptConfig, but it adds a few validation rules
    specific to Airflow
    """

    # NOTE: another validation we can implement would be to create the
    # environment.yml and then make sure we can instantiate the dag, this would
    # allow to verify missing dependencies before exporting rather than when
    # trying to run it in the airflow host
    def validate(self):
        d = self.dict()
        dag = validate_module.project(d)
        validate_module.airflow_pre(d, dag)
