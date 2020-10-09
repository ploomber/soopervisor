"""
Abstract class for executors
"""
import os
from pathlib import Path
import abc


def _check_products_root(product_root, allow_incremental):
    """
    Make sure the product_root folder exists and it's empty.
    Creates a history record based on each hash from the product_root git repo.
    """
    product_root = Path(product_root)

    if not product_root.exists():
        product_root.mkdir(parents=True)

    has_files = bool(os.listdir(str(product_root)))

    if has_files and not allow_incremental:
        raise ValueError(
            f'product_root must be an empty folder ({product_root})')


class Executor(abc.ABC):
    """

    Parameters
    ----------
    script
        Script config object
    """
    def __init__(self, script_config):
        self.project_root = script_config.paths.project
        self.product_root = script_config.paths.products
        self.script_config = script_config

        _check_products_root(self.product_root, self.script_config)

    @abc.abstractmethod
    def execute(self):
        # TODO: must automatically record standard output and error and save
        # NOTE: maybe create a metadata/ folder at the end with the log,
        # the script, optionally the conda env, system info, dag report
        pass

    def __repr__(self):
        return type(self).__name__
