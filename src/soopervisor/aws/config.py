import yaml
from pydantic import BaseModel
from collections.abc import Mapping


class YAMLConfig(BaseModel):
    backend: str

    @classmethod
    def from_file_with_root_key(cls, path, root_key):
        with open(path) as f:
            d = yaml.safe_load(f)

        # TODO: include link to documentation with schema
        if root_key not in d:
            raise KeyError(f'Missing {root_key!r} section in {path}')

        cfg = d[root_key]

        if not isinstance(cfg, Mapping):
            raise TypeError(f'Expected {root_key!r} to be a dictionary, '
                            f'got {type(cfg).__name__}')

        return cls(**cfg)


class AWSBatchConfig(YAMLConfig):
    repository: str
    # must not contain "image"
    container_properties: dict = {
        "memory": 2048,
        "vcpus": 2,
    }
    job_queue: str

    region_name: str

    class Config:
        extra = 'forbid'
