"""
Schema for the (optional) soopervisor.yaml configuration file
"""
import abc
from typing import List

from pydantic import BaseModel
from jinja2 import Template

from soopervisor.base.config import ScriptConfig


class ConfigBaseModel(BaseModel):
    @abc.abstractmethod
    def render(self):
        pass


class ArgoMountedVolume(ConfigBaseModel):
    """
    Volume to mount in the Pod, mounted at /mnt/{claim_name}

    Parameters
    ----------
    claim_name : str
        Claim name for the volume (set in persistentVolumeClaim.claimName)

    sub_path : str
        Sub path from the volume to mount in the Pod (set in subPath). You
        can use the placeholder {{project_name}} which will be automatically
        replaced (e.g. if sub_path='data/{{project_name}}' in a project with
        name 'my_project', it will render to 'data/my_project')

    """
    claim_name: str
    sub_path: str

    def render(self, **kwargs):
        self.sub_path = Template(self.sub_path).render(**kwargs)


class ArgoConfig(ScriptConfig):
    """Configuration for exporting to Argo

    Parameters
    ----------
    mounted_volumes : list
        List of volumes to mount on each Pod (``ArgoMountedVolumes``).
        Defaults to [{'claim_name': 'nfs', 'sub_path': '{{project_name}}'}]

    image : str, default='continuumio/miniconda3'
        Docker image to use

    Notes
    -----
    ``mounted_volumes`` and ``image`` are only used when generating the Argo
    YAML spec and have no bearing during execution, since the YAML espec is
    already created by then

    The first volume in ``mounted_volumes`` is set as the working directory
    for all Pods, make sure it's the volume where the project's source code
    is located
    """
    lazy_import: bool = True

    # TODO: support for secrets https://argoproj.github.io/argo/examples/#secrets
    # NOTE: the storage option is useful here, add support for uploading to
    # google cloud storage

    mounted_volumes: List[ArgoMountedVolume] = [
        ArgoMountedVolume(claim_name='nfs', sub_path='{{project_name}}')
    ]

    image: str = 'continuumio/miniconda3'

    def render(self):
        for mv in self.mounted_volumes:
            mv.render(**dict(project_name=self.project_name))

    @classmethod
    def from_path(cls, project):
        obj = super().from_path(project)
        obj.render()
        return obj
