from pathlib import Path

import yaml


def get_backend(name):
    cfg = yaml.safe_load(Path('soopervisor.yaml').read_text())

    if name not in cfg:
        raise ValueError

    section = cfg[name]

    if 'backend' not in section:
        raise ValueError

    # TODO: validate backend
    return section['backend']
