"""
Online DAG deployment using AWS Lambda
"""
import os
import importlib
from pathlib import Path
import boto3

from jinja2 import Environment, PackageLoader, StrictUndefined
from ploomber.util import default
from ploomber.spec import DAGSpec

from soopervisor import name_format
from soopervisor.aws.util import ScriptExecutor
from soopervisor.aws.config import AWSBatchConfig

_env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                   undefined=StrictUndefined)
_env.filters['to_pascal_case'] = name_format.to_pascal_case

# TODO:
# optionally call "ploomber status" after building image
# what's the best way to specify config files? using sdist?
# how to manage configs? env.dev.yaml, env.prod.yaml


def main(until=None):
    cfg = AWSBatchConfig.from_file_with_root_key('soopervisor.yaml',
                                                 'aws-batch')

    # try to load dag here, to raise an error if there isn't any

    if not Path('setup.py').exists():
        raise ValueError

    # if Path('aws-batch').exists():
    #     raise FileExistsError('aws-batch already exists, Rename or delete '
    #                           'to continue.')

    # if declares_name('tasks.py', 'aws_lambda_submit'):
    #     raise RuntimeError('tasks.py already has a "aws_lambda_submit" '
    #                        'function. Rename or delete to continue.')

    # check setup.py exists in the current dfolder

    pkg_name = default.find_package_name()
    version = importlib.import_module(pkg_name).__version__

    # TODO check if image already exists locally or remotely and skip...

    with ScriptExecutor() as e:
        # e.create_if_not_exists('tasks.py')
        e.inline('rm', '-rf', 'dist/', ' build/', 'aws-batch/')
        e.inline('python', '-m', 'build', '--sdist')

        filename = os.listdir('dist')[0]
        basename = filename.replace('.tar.gz', '')

        # TODO: maybe use dockerfile if it exists? this way users can
        # customize it. otherwise just keep it temporarily and delete it
        # after building. there should also be a way to generate one a leave it
        # there
        e.copy_template('aws-batch/Dockerfile',
                        filename=filename,
                        basename=basename)
        e.inline('cp', '-r', 'dist', 'aws-batch')
        e.inline('cp', 'environment.lock.yml', 'aws-batch')
        # e.append('aws-batch/tasks.py', 'tasks.py')
        e.cd('aws-batch')

        local_name = f'{pkg_name}:{version}'
        # maybe repository should include the type of export?
        # ml-online-aws-batch. or maybe ask at the beginning and save it
        # to soopervisor.yaml if it doesn't exist
        remote_name = f'{cfg.repository}/{pkg_name}:{version}'
        e.inline('docker', 'build', '.', '--tag', local_name)

        if until == 'build':
            return

        e.inline('docker', 'tag', local_name, remote_name)
        e.inline('docker', 'push', remote_name)

        if until == 'push':
            return

        submit(job_def=f'{pkg_name}-{version}'.replace('.', '_'),
               remote_name=remote_name,
               job_queue=cfg.job_queue,
               container_properties=cfg.container_properties)

    print('Done. Files generated at aws-batch/. '
          'See aws-batch/README.md for details')
    print('Added submit command: invoke aws-batch-submit')


def submit(job_def, remote_name, job_queue, container_properties):
    client = boto3.client("batch", region_name='us-east-1')

    container_properties['image'] = remote_name

    print('submitting job definition...')
    client.register_job_definition(jobDefinitionName=job_def,
                                   type='container',
                                   containerProperties=container_properties)

    dag = DAGSpec.find().to_dag()

    job_ids = dict()

    print('Submitting jobs...')
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

    print('Done.')
