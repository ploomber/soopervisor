from collections.abc import Mapping
from pathlib import Path

import yaml

from soopervisor.exceptions import ConfigurationFileTypeError


def read_yaml_mapping(path='soopervisor.yaml'):
    data = yaml.safe_load(Path(path).read_text())

    if not isinstance(data, Mapping):
        raise ConfigurationFileTypeError(path, data)

    return data
