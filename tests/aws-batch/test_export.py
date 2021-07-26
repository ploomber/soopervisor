import os
from unittest.mock import MagicMock, Mock
import json
from pathlib import Path
import shutil

import yaml
import pytest
import moto
import boto3

from soopervisor.aws import batch
from soopervisor.aws.batch import commons
from ploomber.io import _commander, _commander_tester
from ploomber.util import util

service_role = {
    "Version":
    "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "batch.amazonaws.com"
        },
        "Action": "sts:AssumeRole",
    }],
}

instance_role = {
    "Version":
    "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole",
    }],
}


@pytest.fixture
def vpc():
    mock = moto.mock_ec2()
    mock.start()
    ec2 = boto3.resource("ec2", region_name='us-east-1')
    vpc = ec2.create_vpc(CidrBlock="172.16.0.0/16")
    vpc.wait_until_available()
    sub = ec2.create_subnet(CidrBlock="172.16.0.0/24", VpcId=vpc.id)
    sg = ec2.create_security_group(Description="Test security group",
                                   GroupName="sg1",
                                   VpcId=vpc.id)
    yield sg, sub
    mock.stop()


@pytest.fixture
def aws_credentials():
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture()
def batch_client():
    mock = moto.mock_batch()
    mock.start()
    yield boto3.client("batch", region_name='us-east-1')
    mock.stop()


@pytest.fixture
def iam_resource():
    mock = moto.mock_iam()
    mock.start()
    yield boto3.resource("iam", region_name='us-east-1')
    mock.stop()


@pytest.fixture
def mock_batch(aws_credentials, iam_resource, batch_client, vpc):
    sg, sub = vpc

    iam_resource = boto3.resource("iam", region_name='us-east-1')
    batch_client = boto3.client("batch", region_name='us-east-1')

    role = iam_resource.create_role(
        RoleName='role-from-python',
        AssumeRolePolicyDocument=json.dumps(service_role),
        Description='test')

    instance_role_res = iam_resource.create_role(
        RoleName='InstanceRole-from-python',
        AssumeRolePolicyDocument=json.dumps(instance_role),
        Description='test 2')

    ce = batch_client.create_compute_environment(
        computeEnvironmentName='some_environment',
        type='MANAGED',
        computeResources={
            'type': 'EC2',
            'maxvCpus': 8,
            'minvCpus': 4,
            'instanceRole': instance_role_res.arn,
            'instanceTypes': ['c4.large'],
            'securityGroupIds': [
                sg.id,
            ],
            'subnets': [
                sub.id,
            ],
        },
        serviceRole=role.arn,
        state='ENABLED')

    batch_client.create_job_queue(jobQueueName='your-job-queue',
                                  priority=1,
                                  computeEnvironmentOrder=[
                                      {
                                          'computeEnvironment':
                                          ce['computeEnvironmentArn'],
                                          'order':
                                          1,
                                      },
                                  ],
                                  state='ENABLED')
    yield batch_client


def test_error_if_missing_boto3(monkeypatch, backup_packaged_project):

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()

    # simulate boto3 is not installed
    monkeypatch.setattr(util.importlib.util, 'find_spec', lambda _: None)

    with pytest.raises(ImportError) as excinfo:
        exporter.export(mode='incremental')

    assert 'boto3 is required to use AWSBatchExporter' in str(excinfo.value)


def test_add(backup_packaged_project):

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()

    with open('soopervisor.yaml') as f:
        d = yaml.safe_load(f)

    assert d['train'] == {
        'backend': 'aws-batch',
        'repository': 'your-repository/name',
        'job_queue': 'your-job-queue',
        'region_name': 'your-region-name',
        'container_properties': {
            'memory': 16384,
            'vcpus': 8
        }
    }

    assert Path('train', 'Dockerfile').exists()


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


def _monkeypatch_docker(monkeypatch, cmd):
    tester = _commander_tester.CommanderTester(
        run=[
            ('python', '-m', 'build', '--sdist'),
        ],
        return_value={
            ('docker', 'run', 'my_project:0.1dev', 'python', '-c', cmd):
            b'True\n'
        })

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)

    return tester


@pytest.fixture
def monkeypatch_docker(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("src/my_project/pipeline.yaml").to_dag().clients)')
    yield _monkeypatch_docker(monkeypatch, cmd)


@pytest.fixture
def monkeypatch_serve_docker(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("src/my_project/pipeline.serve.yaml").to_dag().clients)')
    yield _monkeypatch_docker(monkeypatch, cmd)


@pytest.mark.parametrize(
    'mode, args',
    [
        ['incremental', []],
        ['regular', []],
        ['force', ['--force']],
    ],
)
def test_export(mock_batch, monkeypatch_docker, monkeypatch,
                backup_packaged_project, mode, args):
    commander_mock = MagicMock()
    monkeypatch.setattr(batch, 'Commander',
                        lambda workspace, templates_path: commander_mock)
    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()
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

    entry = ['--entry-point', 'src/my_project/pipeline.yaml']
    assert commands == {
        'get': ['ploomber', 'task', 'get'] + entry + args,
        'sepal-area': ['ploomber', 'task', 'sepal-area'] + entry + args,
        'petal-area': ['ploomber', 'task', 'petal-area'] + entry + args,
        'features': ['ploomber', 'task', 'features'] + entry + args,
        'fit': ['ploomber', 'task', 'fit'] + entry + args
    }


def test_stops_if_no_tasks(monkeypatch, backup_packaged_project, capsys):
    load_tasks_mock = Mock(return_value=([], ['--entry-point pipeline.yaml']))
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()
    exporter.export(mode='incremental')

    captured = capsys.readouterr()
    assert 'has no tasks to submit.' in captured.out


def test_skip_tests(mock_batch, monkeypatch_docker, monkeypatch,
                    backup_packaged_project, capsys):
    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()
    exporter.export(mode='incremental', skip_tests=True)

    captured = capsys.readouterr()
    assert 'Testing image' not in captured.out
    assert 'Testing File client' not in captured.out


# TODO: check with non-packaged project
def test_checks_the_right_spec(mock_batch, monkeypatch_serve_docker,
                               monkeypatch, backup_packaged_project):
    shutil.copy('src/my_project/pipeline.yaml',
                'src/my_project/pipeline.serve.yaml')

    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'serve')
    exporter.add()
    exporter.export(mode='incremental')

    expected = ('docker', 'run', 'my_project:0.1dev', 'ploomber', 'status',
                '--entry-point', 'src/my_project/pipeline.serve.yaml')
    assert monkeypatch_serve_docker.calls[2] == expected


def test_dockerfile_when_no_setup_py(mock_batch, monkeypatch_docker,
                                     monkeypatch, tmp_sample_project):
    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()

    dockerfile = Path('train', 'Dockerfile').read_text()
    assert 'RUN pip install *.tar.gz --no-deps' not in dockerfile
