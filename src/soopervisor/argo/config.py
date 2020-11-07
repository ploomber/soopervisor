"""
Schema for the (optional) soopervisor.yaml configuration file
"""
from typing import List

from jinja2 import Template

from soopervisor.base.abstract import AbstractBaseModel
from soopervisor.base.config import ScriptConfig


class ArgoMountedVolume(AbstractBaseModel):
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
    YAML spec and have no bearing during execution

    The first volume in ``mounted_volumes`` is set as the working directory
    for all Pods, make sure it's the volume where the project's source code
    is located
    """
    # defaults that we might want to change here
    # ScriptConfig.args should not be allowed, since each script runs a single
    # task and there isn't anything to customize
    # ScriptConfig.executor, do not allow 'docker', just 'local'
    # ScriptConfig.allow_incremental set default to false (?)
    # ScriptConfig.Paths.environment, maybe look for an environment.lock.yml
    # by default
    # ScriptConfig.Storage.path, we don't expect the code in argo to be in a
    # git repo, change "runs/{{git}}" default value

    lazy_import: bool = True

    # TODO: support for secrets https://argoproj.github.io/argo/examples/#secrets
    # NOTE: the storage option is useful here, add support for uploading to
    # google cloud storage

    mounted_volumes: List[ArgoMountedVolume] = [
        ArgoMountedVolume(claim_name='nfs', sub_path='{{project_name}}')
    ]

    image: str = 'continuumio/miniconda3'

    def render(self):
        super().render()

        for mv in self.mounted_volumes:
            mv.render(**dict(project_name=self.project_name))
