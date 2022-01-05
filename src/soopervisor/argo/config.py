from typing import List, Optional

from pydantic import BaseModel

from soopervisor import abc
from soopervisor.enum import Backend


class ArgoMountedVolume(BaseModel):
    """
    Volume to mount in the Pod at ``/mnt/{name}``

    Parameters
    ----------
    name : str
        Volume's name

    sub_path : str, default=''
        Sub path from the volume to mount in the Pod (set in
        ``volumeMounts[*].subPath``). Defaults to the volume's root

    spec : dict
        The volume spec, passed directly to the output spec.
        e.g: ``{'persistentVolumeClaim': {'claimName': 'someName'}}``

    """
    name: str
    sub_path: str = ''
    spec: dict

    class Config:
        extra = 'forbid'

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


class ArgoConfig(abc.AbstractConfig):
    """Configuration for exporting to Argo

    Parameters
    ----------
    repository : str
        Repository for uploading the Docker image.

        .. important::

            If ``repository`` is ``null``, it sets the ``imagePullPolicy`` in
            the generated spec to ``Never``.

    mounted_volumes : list, optional
        List of volumes to mount on each Pod, described with the
        ``ArgoMountedVolumes`` schema.
    """
    repository: Optional[str] = None
    mounted_volumes: Optional[List[ArgoMountedVolume]] = None

    @classmethod
    def get_backend_value(cls):
        return Backend.argo_workflows.value

    @classmethod
    def defaults(cls):
        data = cls(repository='your-repository/name').dict()
        data['backend'] = cls.get_backend_value()
        del data['mounted_volumes']
        del data['include']
        del data['exclude']
        return data
