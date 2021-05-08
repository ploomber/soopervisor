"""
Abstract class for executors
"""
import abc


class Executor(abc.ABC):
    """

    Parameters
    ----------
    script
        Script config object
    """
    def __init__(self, script_config):
        self.project_root = script_config.paths.project
        self.script_config = script_config

    @abc.abstractmethod
    def execute(self):
        # TODO: must automatically record standard output and error and save
        # NOTE: maybe create a metadata/ folder at the end with the log,
        # the script, optionally the conda env, system info, dag report
        pass

    def __repr__(self):
        return type(self).__name__
