import fnmatch
import shutil


def warn_if_not_installed(name):
    if not shutil.which(name):
        print(f'It appears you don\'t have {name} CLI installed, you need it '
              'to execute "invoke aws-lambda build"')


class TaskResources:
    """
    An object to pattern match task names with the task_resources
    section in cloud.yaml
    """
    def __init__(self, mapping):
        self._mapping = mapping

    def get(self, task_name, default=None):
        for pattern, value in self._mapping.items():
            if fnmatch.fnmatch(task_name, pattern):
                return value

        return default
