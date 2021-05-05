from click import ClickException


class ConfigurationError(ClickException):
    """
    Raised when there is a misconfiguration. Captured by the CLI to only
    show the error message and not the whole traceback
    """
    pass
