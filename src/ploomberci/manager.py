def get_git_hash(project_root):
    """Get git has in the project root
    """
    pass


def get_previous_git_hash(project_root):
    """Get git hash from the previous commit
    """
    pass


def is_dirty(project_root):
    """Returns True if there are uncommitted changes
    """
    pass


def restore_previous(product_root):
    """Restore the products from the previous commit
    """
    pass


class ManagerConfig:
    pass


class ExecutionMetadata:
    quasi: bool


class ExecutionHistoryManager:
    """
    Manages executions so each one is uniquely identified by the commit hash
    """
    def execute_current(self):
        """
        Execute current commit
        """
        # NOTE: must not run if the repo is in "dirty" state
        pass