"""
Abstract class for executors
"""
import abc

from ploomberci.check import check_project


class Executor(abc.ABC):
    def __init__(self, project_root):
        check_project(project_root)
        self.project_root(project_root)

    @abc.abstractmethod
    def execute(self):
        pass
