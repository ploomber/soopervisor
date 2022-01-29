from soopervisor.enum import Backend
from soopervisor import abc


class SlurmConfig(abc.AbstractConfig):
    """Configuration for exporting to Slurm
    """

    @classmethod
    def get_backend_value(cls):
        return Backend.slurm.value
