"""
Running pipelines on AWS Batch
"""
import re
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
from soopervisor.commons import docker, source
from soopervisor import commons
from soopervisor import abc
from soopervisor.commons.dependencies import get_default_image_key

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
    image_map,
    job_queue,
    container_properties,
    region_name,
    cmdr,
    is_cloud,
    cfg,
):
    default_image_key = get_default_image_key()
    remote_name = image_map[default_image_key]

    client = boto3.client('batch', region_name=region_name)
    container_properties['image'] = remote_name

    jd_map = {}

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
    jd_map[default_image_key] = jd

    # Register job definitions for task specific images
    for pattern, image in image_map.items():
        if pattern != default_image_key:
            container_props = container_properties.copy()
            container_props['image'] = image
            task_job_def = f"{job_def}-{docker.modify_wildcard(pattern)}"
            cmdr.info(f'Registering {task_job_def!r} job definition...')

            jd = client.register_job_definition(
                jobDefinitionName=task_job_def,
                type='container',
                containerProperties=container_props)
            jd_map[pattern] = jd

    for name, upstream in tasks.items():

        task_pattern = _find_task_pattern(list(image_map.keys()), name)
        task_pattern = task_pattern if task_pattern else default_image_key
        task_jd = jd_map[task_pattern]

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
                                     jobDefinition=task_jd['jobDefinitionArn'],
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
            e.copy_template('aws-batch/Dockerfile',
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists(),
                            lib=Path('lib').exists(),
                            env_name=env_name)
            e.success('Done')
            e.print(
                f'Fill in the configuration in the {env_name!r} '
                'section in soopervisor.yaml then submit to AWS Batch with: '
                f'soopervisor export {env_name}')

        # TODO: run dag checks: client configured, ploomber status

    @classmethod
    @requires(['boto3'], name='AWSBatchExporter')
    def _export(cls, cfg, env_name, mode, until, skip_tests, skip_docker,
                ignore_git, lazy_import, task_name):
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:

            tasks, cli_args = commons.load_tasks(cmdr=cmdr,
                                                 name=env_name,
                                                 mode=mode,
                                                 lazy_import=lazy_import,
                                                 task_name=task_name)

            if not tasks:
                cls._no_tasks_to_submit()
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')
            if skip_docker:
                pkg_name, version = source.find_package_name_and_version()
                default_image_key = get_default_image_key()
                if default_image_key:
                    image_local = f'{pkg_name}:{version}-'
                    f'{docker.modify_wildcard(default_image_key)}'
                image_map = {}
                image_map[default_image_key] = image_local
            else:
                pkg_name, image_map = docker.build(cmdr,
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
                            image_map=image_map,
                            job_queue=cfg.job_queue,
                            container_properties=cfg.container_properties,
                            region_name=cfg.region_name,
                            cmdr=cmdr,
                            cfg=cfg)

            cmdr.success('Done. Submitted to AWS Batch')


def _find_task_pattern(task_patterns, current_task):
    for p in [re.compile(t) for t in task_patterns]:
        if p.match(current_task):
            return p.pattern


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
