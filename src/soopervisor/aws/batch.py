"""
Running pipelines on AWS Batch
"""
import importlib
from pathlib import Path
import boto3

from ploomber.util import default
from ploomber.spec import DAGSpec
from ploomber.io._commander import Commander

from soopervisor.aws.config import AWSBatchConfig

# TODO:
# warn on large distribution artifacts - there might be data files
# make explicit that some errors are happening inside docker

# if pkg is installed --editable, then files inside src/ can find the
# root project without issues but if not they can't,
# perhaps if not project root is found, use the current working directory?

# perhaps scan project for files that are potentially config files and are
# missing from MANIFEST.in?

# how to help users when they've added depedencies via pip/conda but they
# did not add them to setup.py? perhaps export env and look for differences?


def add(name):
    with Commander(workspace=name,
                   templates_path=('soopervisor', 'assets')) as e:
        e.copy_template('aws-batch/Dockerfile')
        e.append('aws-batch/soopervisor.yaml',
                 'soopervisor.yaml',
                 env_name=name)
        e.success(f'Done. Fill in the configuration in the {name!r} '
                  'section in soopervisor.yaml then submit to AWS Batch with: '
                  f'soopervisor submit {name}')


def submit(name, until=None):
    cfg = AWSBatchConfig.from_file_with_root_key('soopervisor.yaml', name)

    dag = DAGSpec.find().to_dag()

    # warn if missing client (only warn cause the config might configure
    # it when building the docker image)

    pkg_name = default.find_package_name()

    # if using versioneer, the version may contain "+"
    version = importlib.import_module(pkg_name).__version__.replace(
        '+', '-plus-')

    # TODO check if image already exists locally or remotely and skip...

    with Commander(workspace=name,
                   templates_path=('soopervisor', 'assets')) as e:
        e.cp('environment.lock.yml')

        # generate source distribution
        # TODO: delete egg-info
        e.rm('dist', 'build')
        e.run('python', '-m', 'build', '--sdist', description='Packaging code')
        e.cp('dist')

        e.cd(name)

        local_name = f'{pkg_name}:{version}'
        # maybe repository should include the type of export?
        # ml-online-aws-batch. or maybe ask at the beginning and save it
        # to soopervisor.yaml if it doesn't exist
        # TODO: validate format of cfg.repository
        remote_name = f'{cfg.repository}:{version}'

        # how to allow passing --no-cache?
        e.run('docker',
              'build',
              '.',
              '--tag',
              local_name,
              description='Building image')

        e.run('docker',
              'run',
              local_name,
              'ploomber',
              'status',
              description='Testing image',
              error_message='Error while testing your docker image with',
              hint=f'Use "docker run -it {local_name} /bin/bash" to '
              'start an interactive session to debug your image')

        test_cmd = ('from ploomber.spec import DAGSpec; '
                    'print("File" in DAGSpec.find().to_dag().clients)')
        e.run('docker',
              'run',
              local_name,
              'python',
              '-c',
              test_cmd,
              description='Testing image',
              error_message='Error while checking File client configuration',
              hint=f'Use "docker run -it {local_name} /bin/bash" to '
              'start an interactive session to debug your image and ensure a '
              'File client is properly configured',
              capture_output=True,
              expected_output='True\n')

        if until == 'build':
            e.print('Done. Run "docker images" to see your image.')
            return

        e.run('docker', 'tag', local_name, remote_name, description='Tagging')
        e.run('docker', 'push', remote_name, description='Pushing image')

        if until == 'push':
            e.print('Done. Image pushed to repository.')
            return

        e.info('Submitting jobs to AWS Batch')

        submit_dag(dag=dag,
                   job_def=f'{pkg_name}-{version}'.replace('.', '_'),
                   remote_name=remote_name,
                   job_queue=cfg.job_queue,
                   container_properties=cfg.container_properties,
                   region_name=cfg.region_name)

        e.success('Submitted to AWS Batch')


def submit_dag(dag, job_def, remote_name, job_queue, container_properties,
               region_name):
    client = boto3.client('batch', region_name=region_name)

    container_properties['image'] = remote_name

    jd = client.register_job_definition(
        jobDefinitionName=job_def,
        type='container',
        containerProperties=container_properties)

    job_ids = dict()

    for name, task in dag.items():
        response = client.submit_job(
            jobName=name,
            jobQueue=job_queue,
            jobDefinition=jd['jobDefinitionArn'],
            dependsOn=[{
                "jobId": job_ids[name]
            } for name in task.upstream],
            containerOverrides={"command": ['ploomber', 'task', name]})

        job_ids[name] = response["jobId"]
