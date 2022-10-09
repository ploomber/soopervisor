"""
Testing docker-related functions. Unlike test_commons.py, this file does not
mock docker
"""
import subprocess
import platform
from pathlib import Path

import pytest
from os import environ

from soopervisor.aws.batch import AWSBatchExporter
from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.airflow.export import AirflowExporter


def _process_docker_output(output):
    """Processes output from "docker build"
    """
    # output (on my local docker) looks like this:

    # STEP 1
    # more stuff
    #
    # STEP 2
    # even more stuff

    lines = output.splitlines()
    sections = []

    # output is separated by an empty line
    empty = [idx for idx, line in enumerate(lines) if line == '']

    # split by each section
    slices = list(zip(empty, empty[1:]))

    for i, j in slices:
        sections.append('\n'.join(lines[i:j]))

    return sections


def _process_docker_output_ci(output):
    lines = output.splitlines()

    sections = []

    step = [idx for idx, line in enumerate(lines) if 'Step ' in line]

    slices = list(zip(step, step[1:]))

    for i, j in slices:
        sections.append('\n'.join(lines[i:j - 1]))

    sections.append('\n'.join(lines[j:]))

    return sections


def test_process_docker_output_ci():
    # this is the format on github actions
    out = """\
Step 1/7 : FROM A
 ---> hash
Step 2/7 : COPY B C
 ---> Using cache
 ---> hash
Step 3/7 : RUN D
 ---> Using cache
 ---> hash
"""

    expected = [
        'Step 1/7 : FROM A',
        'Step 2/7 : COPY B C\n ---> Using cache',
        'Step 3/7 : RUN D\n ---> Using cache\n ---> hash',
    ]

    assert _process_docker_output_ci(out) == expected


config_aws = """\
my-env:
  backend: aws-batch
  container_properties: {memory: 16384, vcpus: 8}
  exclude: [out]
  job_queue: your-job-queue
  region_name: your-region-name
  repository: ploomber.io/repository
"""

config_argo = """\
my-env:
  backend: argo-workflows
  exclude: [out]
  repository: ploomber.io/repository
"""

config_airflow = """\
my-env:
  backend: airflow
  exclude: [out]
  repository: ploomber.io/repository
"""


@pytest.mark.skipif(
    platform.system() != 'Linux' and 'CI' in environ,
    reason="Docker is only installed on the linux runner (Github Actions)",
)
@pytest.mark.parametrize('EXPORTER, config', [
    [AWSBatchExporter, config_aws],
    [ArgoWorkflowsExporter, config_argo],
    [AirflowExporter, config_airflow],
],
                         ids=[
                             'aws',
                             'argo',
                             'airflow',
                         ])
def test_docker_build_caches_pkg_installation(EXPORTER, config,
                                              tmp_fast_pipeline, capfd):
    Path('requirements.lock.txt').write_text('pkgmt==0.0.1')

    with capfd.disabled():
        EXPORTER.new('soopervisor.yaml', env_name='my-env').add()

    Path('soopervisor.yaml').write_text(config)

    with capfd.disabled():
        EXPORTER.load('soopervisor.yaml', env_name='my-env',
                      lazy_import=False).export(mode='incremental',
                                                until='build',
                                                skip_tests=True,
                                                skip_docker=False,
                                                ignore_git=True,
                                                lazy_import=False,
                                                task_name=None)

    EXPORTER.load('soopervisor.yaml', env_name='my-env',
                  lazy_import=False).export(mode='incremental',
                                            until='build',
                                            skip_tests=True,
                                            skip_docker=False,
                                            ignore_git=True,
                                            lazy_import=False,
                                            task_name=None)

    # check that pip installation is cached
    captured = capfd.readouterr()

    # this is the output format on github actions
    if '--->' in captured.err or '--->' in captured.out:
        sections = _process_docker_output_ci(captured.out)
        cached = [group for group in sections if 'Using cache' in group]

    # this is the output format I'm getting locally (macOS)
    # Docker version 20.10.17, build 100c701
    else:
        sections = _process_docker_output(captured.err)
        cached = [group for group in sections if 'CACHED' in group]

    assert len(cached) == 2
    copy = 'COPY requirements.lock.txt project/requirements.lock.txt'
    assert copy in cached[0]
    install = 'RUN pip install --requirement project/requirements.lock.txt'
    assert install in cached[1]

    # check that the packages in the requirements file are installed
    out = subprocess.run(['docker', 'run', 'fast-pipeline', 'pip', 'freeze'],
                         check=True,
                         capture_output=True)

    pkgs = out.stdout.decode()
    assert 'pkgmt==0.0.1' in pkgs

    # check that the right files are copied
    out = subprocess.run(['docker', 'run', 'fast-pipeline', 'ls'],
                         check=True,
                         capture_output=True)

    ls = out.stdout.decode()
    expected = ('environment.yml\nfast-pipeline.tar.gz\n'
                'fast_pipeline.py\nmy-env\npipeline.yaml\n'
                'requirements.lock.txt\nsoopervisor.yaml\n')
    assert ls == expected
