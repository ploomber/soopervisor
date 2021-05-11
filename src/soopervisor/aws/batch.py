"""
Running pipelines on AWS Batch
"""
import boto3

from ploomber.spec import DAGSpec
from ploomber.io._commander import Commander

from soopervisor.aws.config import AWSBatchConfig
from soopervisor.commons import docker

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

# document that only EC2 environments are supported

# TODO: warn if configured client does not have an ID. this means
# artifacts can overwrite if the dag is run more than once at the same time

# add a way to skip tests when submitting


def add(name):
    with Commander(workspace=name,
                   templates_path=('soopervisor', 'assets')) as e:
        e.copy_template('aws-batch/Dockerfile')
        e.append('aws-batch/soopervisor.yaml',
                 'soopervisor.yaml',
                 env_name=name)
        e.success('Done')
        e.print(f'Fill in the configuration in the {name!r} '
                'section in soopervisor.yaml then submit to AWS Batch with: '
                f'soopervisor submit {name}')

        # TODO: run dag checks: client configured, ploomber status


def submit(name, until=None):
    cfg = AWSBatchConfig.from_file_with_root_key('soopervisor.yaml', name)

    dag = DAGSpec.find().to_dag()

    # warn if missing client (only warn cause the config might configure
    # it when building the docker image)

    # TODO check if image already exists locally or remotely and skip...

    with Commander(workspace=name,
                   templates_path=('soopervisor', 'assets')) as e:

        pkg_name, remote_name = docker.build(e, cfg, name, until=until)

        e.info('Submitting jobs to AWS Batch')

        submit_dag(dag=dag,
                   job_def=pkg_name,
                   remote_name=remote_name,
                   job_queue=cfg.submit.job_queue,
                   container_properties=cfg.submit.container_properties,
                   region_name=cfg.submit.region_name,
                   cmdr=e)

        e.success('Done. Submitted to AWS Batch')


def submit_dag(dag, job_def, remote_name, job_queue, container_properties,
               region_name, cmdr):
    client = boto3.client('batch', region_name=region_name)
    container_properties['image'] = remote_name

    cmdr.info(f'Registering {job_def!r} job definition...')
    jd = client.register_job_definition(
        jobDefinitionName=job_def,
        type='container',
        containerProperties=container_properties)

    job_ids = dict()

    cmdr.info('Submitting jobs...')

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
