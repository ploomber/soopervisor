from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator


class BoxConfig(BaseModel):
    # whether to upload to box
    enable: Optional[bool] = False
    # path to box credentials
    # TODO: how to supply credentials if using github actions (env variable?)
    credentials: Optional[str]
    # path to box folder to upload files to
    upload_path: Optional[str]


class ScriptConfig(BaseModel):
    # create env again only if environment.yml has changed
    cache_env: Optional[bool] = True

    project_root: Optional[str] = '.'
    product_root: Optional[str] = 'output'

    # command for running the pipeline
    # TODO: integrate this into script.sh
    command: Optional[str] = 'ploomber build'

    box: Optional[BoxConfig] = BoxConfig()

    @validator('project_root', always=True)
    def project_root_must_be_absolute(cls, v):
        return str(Path(v).resolve())
