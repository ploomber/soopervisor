"""
Schema for the (optional) soopervisor.yaml configuration file
"""
import shutil
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator, Field
from jinja2 import Template
import click
import yaml

from soopervisor.script.script import generate_script
from soopervisor.git_handler import GitRepo
from soopervisor.storage.LocalStorage import LocalStorage
from soopervisor import validate as validate_module


class StorageConfig(BaseModel):
    """Store pipeline products after execution

    Parameters
    ----------
    provider : str, default=None
        'box' for uploading files to box or 'local' to just copy files
        to a local directory. None to disable

    path : str, default='runs/{{git}}'
        Path where the files will be moved, defaults to runs/{{git}},
        where {{git}} will be replaced by the current git hash

    credentials : str, default=None
        Credentials for the storage provider, only required if provider
        is not 'local'
    """
    provider: Optional[str] = None
    path: Optional[str] = 'runs/{{git}}'
    credentials: Optional[str] = None

    # this is not a field, but a reference to the paths section
    paths: Optional[str]

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
    """Coonfiguration schema to execute Ploomber pipelines

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
        Extra arguments to pass to the "ploomber build" command

    paths : dict
        Section to configure project paths, see Paths for schema

    storage : dict
        Section to configure product's upload after execution, see
        StorageConfig for schema
    """
    # TODO: Create env again only if environment.yml has changed
    cache_env: Optional[bool] = False
    executor: Optional[str] = 'local'
    environment_prefix: Optional[str] = None
    allow_incremental: Optional[bool] = True
    args: Optional[str] = ''

    # sub sections
    paths: Optional[Paths] = Field(default_factory=Paths)
    storage: StorageConfig = None

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
    # TODO: Airflow-exclusive parameters, which operator to use (bash,
    # docker, kubernetespod). Maybe template? jinja template where ploomber's
    # code will be generated, in case there is some customization to do for
    # default parameters

    # TODO: some default values should change. for example, look by default
    # for an environment.lock.yml (explain why) and do not set a default
    # to products. lazy_import=True, allow_incremental=False

    # NOTE: another validation we can implement would be to create the
    # environment.yml and then make sure we can instantiate the dag, this would
    # allow to verify missing dependencies before exporting rather than when
    # trying to run it in the airflow host
    def validate(self):
        d = self.dict()
        dag = validate_module.project(d)
        validate_module.airflow_pre(d, dag)


class ArgoConfig(ScriptConfig):
    """Configuration for exporting to Argo
    """
    # there are a few extra parameters to be defined:
    # what persistent colume claim to mount and where
    # is there a way to mount only a specific path?
    # e.g. if the nfs drive has
    # /export/ploomber/{project-name}/{source, output, runs}
    # we could mount /export/ploomber/{project-name}/source to /mnt/vol/source
    # and /export/ploomber/{project-name}/output to /mnt/vol/output

    # TODO: support for secrets https://argoproj.github.io/argo/examples/#secrets

    # NOTE: the storage option is useful here, add support for uploading to
    # google cloud storage
    pass


@click.command()
@click.argument('command')
def _make_script(command):
    # TODO: this should use ArgoConfig
    script = ScriptConfig.from_path('.').to_script(validate=True,
                                                   command=command)
    print(script)


if __name__ == "__main__":
    _make_script()
