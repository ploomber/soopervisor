from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator
import yaml

from ploomberci.script.script import generate_script


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

    @classmethod
    def from_path(cls, project_root):
        """
        Initializes a ScriptConfig from a directory. Looks for a
        project_root/ploomberci.yaml file, if it doesn't exist, it just
        initializes with default values
        """
        path = Path(project_root, 'ploomberci.yaml')

        if path.exists():
            with open(str(path)) as f:
                d = yaml.safe_load(f)

            config = cls(**d)

        else:
            config = cls()

        return config

    def save_script(self):
        """
        Return script (str) and save it at project_root/script.sh
        """
        script = generate_script(config=self)
        Path(self.project_root, 'script.sh').write_text(script)
        return script
