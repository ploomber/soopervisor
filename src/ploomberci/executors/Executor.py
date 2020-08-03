"""
Abstract class for executors
"""
from pathlib import Path
import abc

from ploomberci.check import check_project


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
    """
    def __init__(self, project_root, product_root):
        check_project(project_root)

        if not Path(product_root).is_absolute():
            product_root = Path(project_root, product_root)

        self.project_root = project_root
        self.product_root = product_root

    @abc.abstractmethod
    def execute(self):
        pass
