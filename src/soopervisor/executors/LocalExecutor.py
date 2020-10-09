import subprocess
from soopervisor.executors.Executor import Executor


class LocalExecutor(Executor):
    """
    Execute project in a temporary folder
    """
    def execute(self):
        path_to_script = self.script_config.save_script()

        try:
            subprocess.run(['bash', str(path_to_script)], check=True)
        finally:
            path_to_script.unlink()
