import os

from soopervisor.script.script import generate_script
from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.DockerExecutor import DockerExecutor


def test_run_script(mock_git_hash, tmp_sample_project, tmpdir):
    paths = dict(project=str(tmp_sample_project))
    product_path = tmpdir / "output"

    config = ScriptConfig(paths=paths)
    script = generate_script(config=config)


    docker_params = {
        "project_root": str(tmp_sample_project),
        "product_root": str(product_path),
        "script": script,
    }

    docker_exec = DockerExecutor(**docker_params)

    docker_exec.execute()

    assert bool(os.listdir(str(product_path)))
