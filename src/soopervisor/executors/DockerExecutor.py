import docker
from soopervisor.executors.Executor import Executor


class DockerExecutor(Executor):
    def __init__(self, script_config):
        super().__init__(script_config)
        self.client = docker.from_env()
        self.image = "continuumio/miniconda3"
        self.name = "ploomber"
        self.volumes = {
            self.project_root: {
                "bind": self.project_root,
                "mode": "rw",
            },
            self.product_root: {
                "bind": self.product_root,
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
        self.script_config.save_script()

        project_root = self.project_root.replace(" ", "\ ")

        self.client.containers.run(
            self.image,
            name=self.name,
            volumes=self.volumes,
            command=f"bash {project_root}/script.sh",
        )
