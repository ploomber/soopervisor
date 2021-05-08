"""
Abstract classes that define the protocol for all exporters
"""
import abc
from pathlib import Path


class AbstractConfig:
    """
    Configuration schema
    """
    def __init__(self, path_to_config):
        pass


class AbstractExporter(abc.ABC):
    """

    Parameters
    ----------
    path_to_config : str or pathlib.Path
        Path to the configuration file

    env_name : str
        Environment name
    """
    CONFIG_CLASS = None

    def __init__(self, path_to_config, env_name):
        self._cfg, self._dag = self.CONFIG_CLASS.from_file_with_root_key(
            path_to_config=path_to_config,
            env_name=env_name,
            return_dag=True,
        )
        self._env_name = env_name

        self.validate(self._cfg, self._dag, self._env_name)

    def add(self):
        path = Path(self._env_name)

        if path.exists():
            Path(self._env_name)

            kind = 'file' if path.is_file() else 'directory'
            raise FileExistsError(
                f'A {kind} with name {self._env_name!r} '
                'already exists, delete or rename it and try again')

        path.mkdir()

        return self._add(cfg=self._cfg, env_name=self._env_name)

    def submit(self):
        return self._submit(cfg=self._cfg, env_name=self._env_name)

    @staticmethod
    @abc.abstractmethod
    def validate(cfg, dag):
        """Validate project before generating exported files
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def _add():
        """
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def _submit():
        pass
