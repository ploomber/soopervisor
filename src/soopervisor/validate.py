from pathlib import Path

from soopervisor.exceptions import MissingConfigurationFileError


def value_in(*, name, value, values):
    if value not in values:
        raise ValueError(
            f"{name!r} must be one of {pprint(values)}, got: {value!r}")


def pprint(collection):
    return ', '.join(f"'{element}'" for element in sorted(collection))


def keys(expected, actual, error):
    missing = set(expected) - set(actual)

    if missing:
        raise ValueError(f'{error}: {pprint(missing)}')


def config_file_exists():
    if not Path('soopervisor.yaml').is_file():
        raise MissingConfigurationFileError()
