from pathlib import Path
import os
from soopervisor.base.config import ScriptConfig
from soopervisor.executors.DockerExecutor import DockerExecutor


def test_run_script(git_hash, tmp_sample_project):
    product_path = Path(tmp_sample_project, 'output')

    config = ScriptConfig(paths=dict(project=str(tmp_sample_project)))

    docker_exec = DockerExecutor(config)

    docker_exec.execute()

    assert bool(os.listdir(str(product_path)))
