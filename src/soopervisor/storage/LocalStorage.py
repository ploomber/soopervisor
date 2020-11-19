import os
from pathlib import Path
import shutil


class LocalStorage:
    def __init__(self):
        pass

    def upload(self, from_, to):
        to = Path(to)

        if to.exists():
            if to.is_file():
                raise ValueError(
                    "Storage directory '{}' exists but it's a file".format(to))
            elif len(os.listdir(to)):
                raise ValueError(
                    'Storage directory "{}" is not empty'.format(to))

        shutil.copytree(from_, to)
