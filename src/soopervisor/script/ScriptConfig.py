"""
Schema
------

paths:
    # path to project directory
    project: .
    # path to products directory (if relative, it is to paths.project)
    products: output/
    # path conda environment file (if relative, it is to paths.project)
    environment: environment.yml

storage:
    # storage provider, only "box" is supported for now
    provider: box
    # path where the files will be uploaded, defaults to project/{{git}},
    # where {{git}} will be replaced by the current git hash
    path: projects/{{git}}

"""
import shutil
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator, Field
from jinja2 import Template
import yaml

from soopervisor.script.script import generate_script
from soopervisor import git


class StorageConfig(BaseModel):
    provider: Optional[str] = 'box'
    path: Optional[str] = 'projects/{{git}}'
    enable: Optional[bool] = False
    credentials: Optional[str]

    def __init__(self, *, project, **data) -> None:
        super().__init__(**data)
        self.path = Template(self.path).render(git=git.get_git_hash(project))

    @validator('provider', always=True)
    def project_must_be_absolute(cls, v):
        if v != 'box':
            raise ValueError('Only "box" is supported')
        return v


class Paths(BaseModel):
    project: Optional[str] = '.'
    products: Optional[str] = 'output'
    environment: Optional[str] = 'environment.yml'

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.products = self._resolve_path(self.products)
        self.environment = self._resolve_path(self.environment)

    @validator('project', always=True)
    def project_must_be_absolute(cls, v):
        return str(Path(v).resolve())

    def _resolve_path(self, path):
        if Path(path).is_absolute():
            return str(Path(path).resolve())
        else:
            return str(Path(self.project, path).resolve())


class ScriptConfig(BaseModel):
    paths: Optional[Paths] = Field(default_factory=Paths)

    # create env again only if environment.yml has changed
    cache_env: Optional[bool] = True

    # command for running the pipeline
    # TODO: integrate this into script.sh
    command: Optional[str] = 'ploomber build'

    storage: StorageConfig = None

    def __init__(self, **data) -> None:
        if 'storage' in data:
            storage = data.pop('storage')
        else:
            storage = {}

        super().__init__(**data)
        self.storage = StorageConfig(project=self.paths.products, **storage)

    @classmethod
    def from_path(cls, project):
        """
        Initializes a ScriptConfig from a directory. Looks for a
        project/soopervisor.yaml file, if it doesn't exist, it just
        initializes with default values
        """
        path = Path(project, 'soopervisor.yaml')

        if path.exists():
            with open(str(path)) as f:
                d = yaml.safe_load(f)

            config = cls(**d)

        else:
            config = cls()

        return config

    def to_script(self):
        return generate_script(config=self)

    def save_script(self):
        """
        Return script (str) and save it at project/script.sh
        """
        script = self.to_script()
        Path(self.paths.project, 'script.sh').write_text(script)
        return script

    def clean_products(self):
        if Path(self.paths.products).exists():
            shutil.rmtree(self.paths.products)
            Path(self.paths.products).mkdir()
