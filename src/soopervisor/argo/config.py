"""
Schema for the (optional) soopervisor.yaml configuration file
"""
from typing import List, Optional

from jinja2 import Template

from soopervisor.base.abstract import AbstractBaseModel
from soopervisor.base.config import ScriptConfig


class ArgoMountedVolume(AbstractBaseModel):
    """
    Volume to mount in the Pod at /mnt/{name}

    Parameters
    ----------
    name : str
        Volume's name

    sub_path : str, default=''
        Sub path from the volume to mount in the Pod (set in
        volumeMounts[*].subPath). Use the
        placeholder ``{{project_name}}`` to refer to your project's name
        (e.g. if ``sub_path='data/{{project_name}}'`` in a project named
        'my_project', it will render to 'data/my_project'). Defaults to
        the volume's root

    spec : dict
        The volume spec, passed directly to the output spec.
        e.g: {'persistentVolumeClaim': {'claimName': 'someName'}}

    """
    name: str
    sub_path: str = ''
    spec: dict

    def render(self, **kwargs):
        self.sub_path = Template(self.sub_path).render(**kwargs)

    def to_volume(self):
        """
        Generate the entry for the spec.volumes
        """
        return {'name': self.name, **self.spec}

    def to_volume_mount(self):
        """
        Generate the entry for spec.templates[0].volumeMounts
        """
        # reference: https://argoproj.github.io/argo/fields/#volumemount
        return {
            'name': self.name,
            # by convention, mount to /mnt/ and use the claim name
            'mountPath': f'/mnt/{self.name}',
            'subPath': self.sub_path
        }


class ArgoCodePod(AbstractBaseModel):
    """Configuration to upload code to a Pod with a shared disk mounted

    Parameters
    ----------
    args : str
        Arguments passed to ``kubectl get pods`` to find the pod name to upload
        the code to. Cannot contain the -o/--output option. For example, if
        your disk is located in a pod with role 'nfs-server' in namespace
        'argo', pass ``args='-l role=nfs-server -n argo'``

    path : str
        Path to upload the code to. Use the '{{project_name}}' to replace for
        the project's name
    """
    args: str
    path: str

    def render(self, **kwargs):
        self.path = Template(self.path).render(**kwargs)


class ArgoConfig(ScriptConfig):
    """Configuration for exporting to Argo

    Parameters
    ----------
    mounted_volumes : list
        List of volumes to mount on each Pod, described with the
        ``ArgoMountedVolumes`` schema. Defaults to
        [{'name': 'nfs', 'sub_path': '{{project_name}}',
        'spec': {'persistentVolumeClaim': {'claimName': 'nfs'}}}]

    image : str, default='continuumio/miniconda3'
        Docker image to use

    code_pod : ArgoCodePod, default=None
        Pod for uploading the code, only required if using the ``-u/--upload``
        option when running ``soopervisor export``

    version : str, default=None
        Which soopervisor version to use whhen executing tasks in Argo

    Notes
    -----
    ``mounted_volumes`` and ``image`` are only used when generating the Argo
    YAML spec and have no bearing during execution

    The first volume in ``mounted_volumes`` is set as the working directory
    for all Pods, make sure it's the volume where the project's source code
    is located

    Unlike the base settings default, ``lazy_import`` is set to ``True`` by
    default
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
        ArgoMountedVolume(
            name='nfs',
            sub_path='{{project_name}}',
            spec=dict(persistentVolumeClaim=dict(claimName='nfs')))
    ]

    code_pod: Optional[ArgoCodePod] = None

    image: str = 'continuumio/miniconda3'

    def render(self):
        super().render()

        for mv in self.mounted_volumes:
            mv.render(project_name=self.project_name)

        if self.code_pod is not None:
            self.code_pod.render(project_name=self.project_name)
