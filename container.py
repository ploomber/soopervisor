"""
imdb is for non-commercial use, find another dataset

User:

* Register github urls

Then:

* Clone repo on a clean instance
* Check if all needed files exist:
    * environment.yml
    * setup.py
* Lauch container
* Get latest (per branch) environment that succeeded and mount it
* Install conda
* Instal env using environment.yml, run pip install ".[dev]"
* Run pytest
* If succeeds, keep environment and mark it as the "last successful"
* If fails - keep it for debugging reasons
"""
import shutil
from git import Repo
from pathlib import Path
import docker


def run_in_container(hash_, branch, url, workspace):
    workspace_tmp = Path(workspace, branch, hash_)
    Repo.clone_from(url, workspace_tmp)

    shutil.copy('setup.sh', str(workspace_tmp / 'setup.sh'))

    client = docker.from_env()
    client.containers.run("continuumio/miniconda3", "bash /mnt/vol1/setup.sh",
                          volumes={str(workspace_tmp):
                                   {'bind': '/mnt/vol1', 'mode': 'ro'}},
                          stream=True)
