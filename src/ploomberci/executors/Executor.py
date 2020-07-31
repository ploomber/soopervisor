"""
Abstract class for executors
"""
import os
from pathlib import Path
import abc

from ploomberci.check import check_project


def handle_product_root(product_root):
    """
    Make sure the product_root folder exists and it's empty
    """
    product_root = Path(product_root)

    if product_root.exists():
        has_files = bool(os.listdir(str(product_root)))

        if has_files:
            raise ValueError('product_root must be an empty folder')
    else:
        product_root.mkdir(parents=True)


class Executor(abc.ABC):
    """

    Parameters
    ----------
    project_root : str
        Directory where pipeline.yaml is located and the working directory
        where the project will be executed

    product_root : str
        Directory where all pipeline products are saved upon execution. If
        relative, it is interpreted as relative to project_root

    script : str
        The the script to run
    """
    def __init__(self, project_root, product_root, script):
        check_project(project_root)
        handle_product_root(product_root)

        if not Path(product_root).is_absolute():
            product_root = Path(project_root, product_root)

        self.project_root = project_root
        self.product_root = product_root
        self.script = script

    @abc.abstractmethod
    def execute(self):
        pass
