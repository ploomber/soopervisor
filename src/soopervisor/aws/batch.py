"""
Running pipelines on AWS Batch
"""
from uuid import uuid4
import os
import json
from pathlib import Path
import fnmatch

from ploomber.io._commander import Commander, CommanderStop
from ploomber.util.util import requires
from ploomber.cloud import api

from soopervisor.aws.config import AWSBatchConfig, CloudConfig
from soopervisor.aws.util import TaskResources
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


# FIXME: move this logic to ploomber so we validate it
# before and after we submit the code
def _transform_task_resources(resources):
    resources_out = []

    if resources.vcpus:
        resources_out.append({'value': str(resources.vcpus), 'type': 'VCPU'})

    if resources.memory:
        resources_out.append({
            'value': str(resources.memory),
            'type': 'MEMORY'
        })

    if resources.gpu:
        resources_out.append({'value': str(resources.gpu), 'type': 'GPU'})

    return resources_out


def _validate_keys(task_resources, tasks):
    names = list(tasks)

    faulty_keys = []

    # validate that all keys in task_resources match at least one task name
    for pattern in task_resources:
        matches = fnmatch.filter(names, pattern)

        if not matches:
            faulty_keys.append(pattern)

    if faulty_keys:
        faulty_keys_out = '\n* '.join(faulty_keys)
        raise ValueError('The following keys in the task_resources section '
                         'did not match any pipeline tasks. Delete them '
                         'or ensure they match at least one task '
                         f'name:\n{faulty_keys_out}')


def _process_task_resources(task_resources, tasks):
    if not task_resources:
        return {}

    _validate_keys(task_resources, tasks)

    return TaskResources({
        key: _transform_task_resources(value)
        for key, value in task_resources.items()
    })


def _submit_dag(
    tasks,
    args,
    job_def,
    remote_name,
    job_queue,
    container_properties,
    region_name,
    cmdr,
    is_cloud,
    cfg,
):
    client = boto3.client('batch', region_name=region_name)
    container_properties['image'] = remote_name

    task_resources = _process_task_resources(cfg.task_resources, tasks)

    cmdr.info(f'Registering {job_def!r} job definition...')

    job_ids = dict()

    cmdr.info('Submitting jobs...')

    if is_cloud:
        # docker.build moves to the env folder
        params = json.loads(Path('../.ploomber-cloud').read_text())

        # note: this will trigger an error if the user has no quota left
        out = api.runs_update(params['runid'], tasks)
    else:
        out, params = None, None

    jd = client.register_job_definition(
        jobDefinitionName=job_def,
        type='container',
        containerProperties=container_properties)

    for name, upstream in tasks.items():

        if is_cloud:
            ploomber_task = [
                'python',
                '-m',
                'ploomber.cli.task',
                name,
                '--task-id',
                out['taskids'][name],
            ]

            container_overrides = {
                "command":
                ploomber_task + args,
                "environment": [
                    {
                        "name": "PLOOMBER_CLOUD_KEY",
                        "value": os.environ["PLOOMBER_CLOUD_KEY"]
                    },
                    {
                        "name": "PLOOMBER_CLOUD_HOST",
                        "value": os.environ["PLOOMBER_CLOUD_HOST"]
                    },
                ]
            }

        else:
            ploomber_task = ['ploomber', 'task', name]
            container_overrides = {"command": ploomber_task + args}

        # add requested resources
        container_overrides['resourceRequirements'] = task_resources.get(
            name, [])

        response = client.submit_job(jobName=name,
                                     jobQueue=job_queue,
                                     jobDefinition=jd['jobDefinitionArn'],
                                     dependsOn=[{
                                         "jobId": job_ids[name]
                                     } for name in upstream],
                                     containerOverrides=container_overrides)

        job_ids[name] = response["jobId"]

        cmdr.print(f'Submitted task {name!r}...')

    if is_cloud:
        api.runs_register_ids(params['runid'], job_ids)


class AWSBatchExporter(abc.AbstractExporter):
    CONFIG_CLASS = AWSBatchConfig

    @classmethod
    def _submit_dag(cls, *args, **kwargs):
        return _submit_dag(*args, **kwargs, is_cloud=False)

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @classmethod
    def _no_tasks_to_submit(cls):
        pass

    @staticmethod
    def _add(cfg, env_name):
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('docker/Dockerfile',
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists(),
                            env_name=env_name)
            e.success('Done')
            e.print(
                f'Fill in the configuration in the {env_name!r} '
                'section in soopervisor.yaml then submit to AWS Batch with: '
                f'soopervisor export {env_name}')

        # TODO: run dag checks: client configured, ploomber status

    @classmethod
    @requires(['boto3'], name='AWSBatchExporter')
    def _export(cls, cfg, env_name, mode, until, skip_tests, ignore_git,
                lazy_import):
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:
            tasks, cli_args = commons.load_tasks(cmdr=cmdr,
                                                 name=env_name,
                                                 mode=mode,
                                                 lazy_import=lazy_import)

            if not tasks:
                cls._no_tasks_to_submit()
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

            # add a unique suffix to prevent collisions
            suffix = str(uuid4())[:8]
            cls._submit_dag(tasks=tasks,
                            args=cli_args,
                            job_def=f'{pkg_name}-{suffix}',
                            remote_name=remote_name,
                            job_queue=cfg.job_queue,
                            container_properties=cfg.container_properties,
                            region_name=cfg.region_name,
                            cmdr=cmdr,
                            cfg=cfg)

            cmdr.success('Done. Submitted to AWS Batch')


# TODO: add tests
class CloudExporter(AWSBatchExporter):
    CONFIG_CLASS = CloudConfig

    @classmethod
    def _no_tasks_to_submit(cls):
        params = json.loads(Path('.ploomber-cloud').read_text())
        api.run_finished(params['runid'])

    @classmethod
    def _submit_dag(cls, *args, **kwargs):
        return _submit_dag(*args, **kwargs, is_cloud=True)
