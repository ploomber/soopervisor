import yaml
from pydantic import BaseModel


class YAMLConfig(BaseModel):
    @classmethod
    def from_file_with_root_key(cls, path, root_key):
        with open(path) as f:
            d = yaml.safe_load(f)

        return cls(**d[root_key])


class AWSBatchConfig(YAMLConfig):
    repository: str
    # must not contain "image"
    container_properties: dict = {
        "memory": 2048,
        "vcpus": 2,
    }
    job_queue: str

    class Config:
        extra = 'forbid'
