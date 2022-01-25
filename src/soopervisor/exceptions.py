from pathlib import Path

from click import ClickException


class ConfigurationError(ClickException):
    """
    Raised when there is a misconfiguration. Captured by the CLI to only
    show the error message and not the whole traceback
    """
    pass


class MissingDockerfileError(ClickException):
    """
    Raised when trying to build a Docker image but the DockerFile is missing
    """
    def __init__(self, env_name):
        self.env_name = env_name
        path = str(Path(env_name, 'Dockerfile'))
        message = f"""\
Expected Dockerfile at {path!r} but it does not exist\
        """
        super().__init__(message)
