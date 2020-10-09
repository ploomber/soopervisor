import os
from pathlib import Path


class LocalStorage:
    def __init__(self, path):
        self.path = Path(path)

        if self.path.exists():
            if self.path.is_file():
                raise ValueError(
                    "Storage directory '{}' exists but it's a file".format(
                        self.path))
            elif len(os.listdir(self.path)):
                raise ValueError('Storage directory "{}" is not empty'.format(
                    self.path))
