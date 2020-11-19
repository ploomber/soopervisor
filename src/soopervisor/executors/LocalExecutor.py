from pathlib import Path
import subprocess
from soopervisor.executors.Executor import Executor


class LocalExecutor(Executor):
    """
    Execute project locally
    """
    def execute(self):
        path_to_script = self.script_config.save_script()

        try:
            subprocess.run(['bash', path_to_script], check=True)
        finally:
            Path(path_to_script).unlink()
