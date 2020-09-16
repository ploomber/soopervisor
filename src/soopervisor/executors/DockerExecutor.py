import docker
from pathlib import Path
from soopervisor.executors.Executor import Executor


class DockerExecutor(Executor):
    def __init__(self, project_root, product_root, script):
        super().__init__(project_root, product_root, script)
        self.client = docker.from_env()
        self.image = "continuumio/miniconda3"
        self.name = "ploomber"
        self.volumes = {
            self.project_root: {
                "bind": self.project_root,
                "mode": "rw",
            },
            self.product_root: {
                "bind": f"{self.project_root}/output",
                "mode": "rw",
            },
        }

        self._remove_default_container()

    def _remove_default_container(self):
        """
        In case the docker container already exists, it is removed.
        """
        try:
            ploomber_container = self.client.containers.get(self.name)
            ploomber_container.remove(force=True)
        except docker.errors.NotFound:
            print("Environment ready to run pipeline")

    def execute(self):
        path_to_script = Path(self.project_root, 'script.sh')
        path_to_script.write_text(self.script)
        project_root = self.project_root.replace(" ", "\ ")
        self.client.containers.run(
            self.image,
            name=self.name,
            volumes=self.volumes,
            command=f"bash {project_root}/script.sh",
        )
