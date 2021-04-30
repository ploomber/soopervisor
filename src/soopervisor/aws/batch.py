"""
Online DAG deployment using AWS Lambda
"""
import os
import importlib
from pathlib import Path
import boto3

from ploomber.util import default
from ploomber.spec import DAGSpec
from ploomber.io._commander import Commander

from soopervisor.aws.config import AWSBatchConfig

# TODO:
# how to manage configs? env.dev.yaml, env.prod.yaml
# warn on large distribution artifacts - there might be data files
# make explicit that some errors are happening inside docker

# if pkg is installed --editable, then files inside src/ can find the
# root project without issues but if not they can't,
# perhaps if not project root is found, use the current working directory?

# perhaps scan project for files that are potentially config files and are missing from MANIFEST.in?

# how to help users when they've added depedencies via pip/conda but they
# did not add them to setup.py? perhaps export env and look for differences?


def main(until=None):
    cfg = AWSBatchConfig.from_file_with_root_key('soopervisor.yaml',
                                                 'aws-batch')

    dag = DAGSpec.find().to_dag()

    # warn if missing client (only warn cause the config might configure
    # it when building the docker image)

    if not Path('setup.py').exists():
        raise ValueError

    # check setup.py exists in the current dfolder

    pkg_name = default.find_package_name()
    version = importlib.import_module(pkg_name).__version__

    # TODO check if image already exists locally or remotely and skip...

    with Commander(workspace='aws-batch',
                   templates_path=('soopervisor', 'assets')) as e:
        # e.create_if_not_exists('tasks.py')
        e.run('rm -rf dist/  build/', description='Cleaning up')
        e.run('python -m build --sdist', description='Packaging')

        filename = os.listdir('dist')[0]
        basename = filename.replace('.tar.gz', '')

        # TODO: maybe use dockerfile if it exists? this way users can
        # customize it. otherwise just keep it temporarily and delete it
        # after building. there should also be a way to generate one a leave it
        # there
        e.copy_template('aws-batch/Dockerfile',
                        filename=filename,
                        basename=basename)

        e.cp('dist', 'aws-batch/dist')
        e.cp('environment.lock.yml', 'aws-batch')

        e.cd('aws-batch')

        local_name = f'{pkg_name}:{version}'
        # maybe repository should include the type of export?
        # ml-online-aws-batch. or maybe ask at the beginning and save it
        # to soopervisor.yaml if it doesn't exist
        remote_name = f'{cfg.repository}/{pkg_name}:{version}'
        e.run(f'docker build . --tag {local_name}',
              description='Building image...')

        e.run(f'docker run {local_name} ploomber status',
              description='Testing')

        out = e.run(
            f'docker run {local_name} python -c '
            '"from ploomber.spec import DAGSpec; '
            'print(\'File\' in DAGSpec.find().to_dag().clients)"',
            description='h',
            capture_output=True)

        # TODO: change, this is no loner bytes but a str obj
        if out == 'False\n':
            raise RuntimeError(
                'Missing client for Files in Docker build. '
                'Ensure a client for Files is properly configured '
                'in pipeline.yaml')

        if until == 'build':
            e.tw.write('Done. Run "docker images" to see your image.')
            return

        e.run(f'docker tag {local_name} {remote_name}', description='Tagging')
        e.run(f'docker push {remote_name}', description='Pushing image')

        if until == 'push':
            e.tw.write('Done. Image pushed to repository.')
            return

        e.tw.sep('=', 'Submitting jobs to AWS Batch', blue=True)

        submit(dag=dag,
               job_def=f'{pkg_name}-{version}'.replace('.', '_'),
               remote_name=remote_name,
               job_queue=cfg.job_queue,
               container_properties=cfg.container_properties)

        e.tw.sep('=', 'Submitted to AWS Batch', green=True)


def submit(dag, job_def, remote_name, job_queue, container_properties):
    client = boto3.client("batch", region_name='us-east-1')

    container_properties['image'] = remote_name

    client.register_job_definition(jobDefinitionName=job_def,
                                   type='container',
                                   containerProperties=container_properties)

    job_ids = dict()

    for name, task in dag.items():
        response = client.submit_job(
            jobName=name,
            jobQueue=job_queue,
            jobDefinition=job_def,
            dependsOn=[{
                "jobId": job_ids[name]
            } for name in task.upstream],
            containerOverrides={"command": ['ploomber', 'task', name]})

        job_ids[name] = response["jobId"]
