from pathlib import Path

from click import ClickException


def _comma_separated(values):
    return ', '.join([repr(v) for v in values])


class BackendWithoutPresetsError(ClickException):
    """Raises when passing a preset to a backend doesn't have any
    """

    def __init__(self, backend):
        super().__init__(f'Backend {str(backend)!r} does not have '
                         'presets. Remove the argument.')


class InvalidPresetForBackendError(ClickException):
    """Raised if the passed preset is not valid for the passed backend
    """

    def __init__(self, backend, preset, preset_values):
        super().__init__(f'Preset {preset!r} is not a valid value for '
                         f'backend {str(backend)!r}. Valid presets are: '
                         f'{_comma_separated(preset_values)}')


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
