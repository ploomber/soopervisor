"""
Running pipelines on AWS Batch
"""
from pathlib import Path

from ploomber.io._commander import Commander, CommanderStop
from ploomber.util.util import requires

from soopervisor.aws.config import AWSBatchConfig
from soopervisor.commons import docker
from soopervisor import commons
from soopervisor import abc

try:
    import boto3
except ModuleNotFoundError:
    boto3 = None

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


class AWSBatchExporter(abc.AbstractExporter):
    CONFIG_CLASS = AWSBatchConfig

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @staticmethod
    def _add(cfg, env_name):
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('aws-batch/Dockerfile',
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists())
            e.success('Done')
            e.print(
                f'Fill in the configuration in the {env_name!r} '
                'section in soopervisor.yaml then submit to AWS Batch with: '
                f'soopervisor export {env_name}')

        # TODO: run dag checks: client configured, ploomber status

    @staticmethod
    @requires(['boto3'], name='AWSBatchExporter')
    def _export(cfg, env_name, mode, until, skip_tests, ignore_git):
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:
            tasks, cli_args = commons.load_tasks(cmdr=cmdr,
                                                 name=env_name,
                                                 mode=mode)

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            pkg_name, remote_name = docker.build(cmdr,
                                                 cfg,
                                                 env_name,
                                                 until=until,
                                                 entry_point=cli_args[1],
                                                 skip_tests=skip_tests,
                                                 ignore_git=ignore_git)

            cmdr.info('Submitting jobs to AWS Batch')

            submit_dag(tasks=tasks,
                       args=cli_args,
                       job_def=pkg_name,
                       remote_name=remote_name,
                       job_queue=cfg.job_queue,
                       container_properties=cfg.container_properties,
                       region_name=cfg.region_name,
                       cmdr=cmdr)

            cmdr.success('Done. Submitted to AWS Batch')


def submit_dag(
    tasks,
    args,
    job_def,
    remote_name,
    job_queue,
    container_properties,
    region_name,
    cmdr,
):
    client = boto3.client('batch', region_name=region_name)
    container_properties['image'] = remote_name

    cmdr.info(f'Registering {job_def!r} job definition...')
    jd = client.register_job_definition(
        jobDefinitionName=job_def,
        type='container',
        containerProperties=container_properties)

    job_ids = dict()

    cmdr.info('Submitting jobs...')

    for name, upstream in tasks.items():
        response = client.submit_job(
            jobName=name,
            jobQueue=job_queue,
            jobDefinition=jd['jobDefinitionArn'],
            dependsOn=[{
                "jobId": job_ids[name]
            } for name in upstream],
            containerOverrides={"command": ['ploomber', 'task', name] + args})

        job_ids[name] = response["jobId"]

        cmdr.print(f'Submitted task {name!r}...')
