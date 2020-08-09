from pathlib import Path
import subprocess
from soopervisor.executors.Executor import Executor


class LocalExecutor(Executor):
    """
    Execute project in a temporary folder
    """
    def execute(self):
        path_to_script = Path(self.project_root, 'script.sh')
        path_to_script.write_text(self.script)

        try:
            subprocess.run(['bash', 'script.sh'], check=True)
        except Exception:
            path_to_script.unlink()
            raise
