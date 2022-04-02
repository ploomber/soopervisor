from unittest.mock import MagicMock, Mock
from pathlib import Path
import shutil

from pydantic import ValidationError
import yaml
import pytest
import boto3

from soopervisor.aws import batch
from soopervisor.aws.batch import commons
from ploomber.util import util


def test_error_if_missing_boto3(monkeypatch, backup_packaged_project):

    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'train')
    exporter.add()

    # simulate boto3 is not installed
    monkeypatch.setattr(util.importlib.util, 'find_spec', lambda _: None)

    with pytest.raises(ImportError) as excinfo:
        exporter.export(mode='incremental')

    assert ("'boto3' is required to use 'AWSBatchExporter'"
            in str(excinfo.value))


def process_submit_job_call(call):
    """Process a call to boto3.submit_job to index by task name
    """
    try:
        # py 3.6, 3.7
        kw = call[1]
    except KeyError:
        # py >3.7
        kw = call.kwargs

    return {
        kw['jobName']: {
            'dependsOn': [dep['jobId'] for dep in kw['dependsOn']],
            'containerOverrides': kw['containerOverrides']
        }
    }


def index_submit_job_by_task_name(calls):
    """Index all calls to boto3.submit_job by task name
    """
    calls = [process_submit_job_call(c) for c in calls]
    return {k: v for d in calls for k, v in d.items()}


def index_by(d, index_by, value_from_key):
    """
    Extract a key from a dictionary and assign the value to the one from
    another key
    """
    return {d[index_by]: d[value_from_key]}


def merge_dicts(dicts):
    """Merge dictionaries into one
    """
    return {k: v for d in dicts for k, v in d.items()}


def index_job_name_by_id(jobs_info):
    """Create a mapping from job id to name from jobs info
    """
    return merge_dicts(
        index_by(info, index_by='jobId', value_from_key='jobName')
        for info in jobs_info)


def index_dependencies_by_name(submitted, id2name):
    return {
        name: set(id2name[id_] for id_ in val['dependsOn'])
        for name, val in submitted.items()
    }


def index_commands_by_name(submitted):
    return {
        key: val['containerOverrides']['command']
        for key, val in submitted.items()
    }


@pytest.mark.parametrize(
    'mode, args',
    [
        ['incremental', []],
        ['regular', []],
        ['force', ['--force']],
    ],
)
def test_export(mock_batch, mock_docker_my_project_serve, monkeypatch,
                monkeypatch_docker_client, backup_packaged_project, mode, args,
                skip_repo_validation):
    p_home_mock = Mock()
    monkeypatch.setattr(commons.docker, 'cp_ploomber_home', p_home_mock)
    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'train')
    exporter.add()

    # mock commander
    commander_mock = MagicMock()
    monkeypatch.setattr(batch, 'Commander',
                        lambda workspace, templates_path: commander_mock)

    exporter.export(mode=mode)

    jobs = mock_batch.list_jobs(jobQueue='your-job-queue')['jobSummaryList']

    # get jobs information
    jobs_info = mock_batch.describe_jobs(jobs=[job['jobId']
                                               for job in jobs])['jobs']

    load_tasks_mock.assert_called_once_with(cmdr=commander_mock.__enter__(),
                                            name='train',
                                            mode=mode)

    submitted = index_submit_job_by_task_name(
        boto3_mock.submit_job.call_args_list)
    id2name = index_job_name_by_id(jobs_info)

    dependencies = index_dependencies_by_name(submitted, id2name)
    commands = index_commands_by_name(submitted)

    # check all tasks submitted
    assert {j['jobName']
            for j in jobs_info
            } == {'features', 'fit', 'get', 'petal-area', 'sepal-area'}

    # check submitted to the right queue
    assert all(['your-job-queue' in j['jobQueue'] for j in jobs_info])

    # check created a job definition with the right name
    assert all(['my_project:1' in j['jobDefinition'] for j in jobs_info])

    assert dependencies == {
        'get': set(),
        'sepal-area': {'get'},
        'petal-area': {'get'},
        'features': {'get', 'petal-area', 'sepal-area'},
        'fit': {'features'}
    }

    entry = ['--entry-point', str(Path('src', 'my_project', 'pipeline.yaml'))]
    assert commands == {
        'get': ['ploomber', 'task', 'get'] + entry + args,
        'sepal-area': ['ploomber', 'task', 'sepal-area'] + entry + args,
        'petal-area': ['ploomber', 'task', 'petal-area'] + entry + args,
        'features': ['ploomber', 'task', 'features'] + entry + args,
        'fit': ['ploomber', 'task', 'fit'] + entry + args
    }


# TODO: check with non-packaged project
def test_checks_the_right_spec(mock_batch, mock_docker_my_project_serve,
                               monkeypatch, monkeypatch_docker_client,
                               backup_packaged_project, skip_repo_validation):
    shutil.copy('src/my_project/pipeline.yaml',
                'src/my_project/pipeline.serve.yaml')

    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)

    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'serve')
    exporter.add()
    exporter.export(mode='incremental')

    expected = ('docker', 'run', 'my_project:0.1dev', 'ploomber', 'status',
                '--entry-point',
                str(Path('src', 'my_project', 'pipeline.serve.yaml')))
    assert mock_docker_my_project_serve.calls[2] == expected


@pytest.fixture
def mock_aws_batch(mock_batch, mock_docker_my_project_serve, monkeypatch,
                   monkeypatch_docker_client, backup_packaged_project,
                   skip_repo_validation):
    p_home_mock = Mock()
    monkeypatch.setattr(commons.docker, 'cp_ploomber_home', p_home_mock)
    batch_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: batch_mock)
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    return batch_mock


@pytest.mark.parametrize('task_resources, resource_requirements', [
    [
        {
            'fit': {
                'vcpus': 32,
                'memory': 32768
            },
            'get': {
                'vcpus': 4,
                'memory': 4096
            }
        },
        {
            'fit': [
                {
                    'value': '32',
                    'type': 'VCPU'
                },
                {
                    'value': '32768',
                    'type': 'MEMORY'
                },
            ],
            'get': [
                {
                    'value': '4',
                    'type': 'VCPU'
                },
                {
                    'value': '4096',
                    'type': 'MEMORY'
                },
            ]
        },
    ],
    [
        {
            'fit': {
                'vcpus': 32,
                'memory': 32768
            }
        },
        {
            'fit': [
                {
                    'value': '32',
                    'type': 'VCPU'
                },
                {
                    'value': '32768',
                    'type': 'MEMORY'
                },
            ]
        },
    ],
    [
        {
            'fit': {
                'vcpus': 32,
                'memory': 32768,
                'gpu': 2,
            }
        },
        {
            'fit': [
                {
                    'value': '32',
                    'type': 'VCPU'
                },
                {
                    'value': '32768',
                    'type': 'MEMORY'
                },
                {
                    'value': '2',
                    'type': 'GPU'
                },
            ]
        },
    ],
])
def test_custom_task_resources(mock_aws_batch, monkeypatch, task_resources,
                               resource_requirements):
    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'train')
    exporter.add()

    # customize soopervisor.yaml
    config = yaml.safe_load(Path('soopervisor.yaml').read_text())
    config['train']['task_resources'] = task_resources
    Path('soopervisor.yaml').write_text(yaml.dump(config))

    # mock commander
    commander_mock = MagicMock()
    monkeypatch.setattr(batch, 'Commander',
                        lambda workspace, templates_path: commander_mock)

    # reload exporter to force reloading soopervisor.yaml
    exporter = batch.AWSBatchExporter.load(path_to_config='soopervisor.yaml',
                                           env_name='train')
    exporter.export(mode='incremental')

    submitted = index_submit_job_by_task_name(
        mock_aws_batch.submit_job.call_args_list)

    reqs_fit = submitted['fit']['containerOverrides']['resourceRequirements']
    assert reqs_fit == resource_requirements['fit']

    reqs_get = submitted['get']['containerOverrides']['resourceRequirements']
    assert reqs_get == resource_requirements.get('get', [])


def test_validates_task_resources(mock_aws_batch):
    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'train')
    exporter.add()

    # customize soopervisor.yaml
    config = yaml.safe_load(Path('soopervisor.yaml').read_text())
    config['train']['task_resources'] = {
        'fit': {
            'vcpusss': 32,
            'memory': 32768,
        }
    }
    Path('soopervisor.yaml').write_text(yaml.dump(config))

    with pytest.raises(ValidationError):
        batch.AWSBatchExporter.load(path_to_config='soopervisor.yaml',
                                    env_name='train')


def test_validates_names_in_task_resources(mock_aws_batch, monkeypatch):
    exporter = batch.AWSBatchExporter.new('soopervisor.yaml', 'train')
    exporter.add()

    # customize soopervisor.yaml
    config = yaml.safe_load(Path('soopervisor.yaml').read_text())
    config['train']['task_resources'] = {
        'not-a-task': {
            'vcpus': 32,
            'memory': 32768,
        }
    }
    Path('soopervisor.yaml').write_text(yaml.dump(config))

    # mock commander
    commander_mock = MagicMock()
    monkeypatch.setattr(batch, 'Commander',
                        lambda workspace, templates_path: commander_mock)

    # reload exporter to force reloading soopervisor.yaml
    exporter = batch.AWSBatchExporter.load(path_to_config='soopervisor.yaml',
                                           env_name='train')

    with pytest.raises(ValueError) as excinfo:
        exporter.export(mode='incremental')

    assert ("Unexpected task names in task_resources" in str(excinfo.value))
