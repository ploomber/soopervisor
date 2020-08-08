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
