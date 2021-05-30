import os
from unittest.mock import Mock
import json
from pathlib import Path

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


@pytest.fixture()
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


@pytest.fixture()
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


def test_export(mock_batch, monkeypatch, backup_packaged_project):
    Path('setup.py').unlink()

    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in DAGSpec.find().to_dag().clients)')
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

    boto3_mock = Mock(wraps=boto3.client('batch', region_name='us-east-1'))
    monkeypatch.setattr(batch.boto3, 'client',
                        lambda name, region_name: boto3_mock)
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()
    exporter.export()

    jobs = mock_batch.list_jobs(jobQueue='your-job-queue')['jobSummaryList']

    jobs_info = mock_batch.describe_jobs(jobs=[job['jobId']
                                               for job in jobs])['jobs']

    load_tasks_mock.assert_called_once_with(incremental=True)

    assert {j['jobName']
            for j in jobs_info
            } == {'features', 'fit', 'get', 'petal-area', 'sepal-area'}

    def process_call(call):
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

    calls = [process_call(c) for c in boto3_mock.submit_job.call_args_list]
    calls = {k: v for d in calls for k, v in d.items()}

    def process_dict(d, index_by, include_keys):
        if isinstance(include_keys, str):
            return {d[index_by]: d[include_keys]}
        else:
            return {d[index_by]: {k: d[k] for k in include_keys}}

    def merge_dicts(dicts):
        return {k: v for d in dicts for k, v in d.items()}

    id2name = merge_dicts(
        process_dict(info, index_by='jobId', include_keys='jobName')
        for info in jobs_info)

    assert calls['get']['dependsOn'] == []
    assert {id2name[dep]
            for dep in calls['petal-area']['dependsOn']} == {'get'}
    assert {id2name[dep]
            for dep in calls['sepal-area']['dependsOn']} == {'get'}
    assert {id2name[dep]
            for dep in calls['features']['dependsOn']
            } == {'get', 'sepal-area', 'petal-area'}
    assert {id2name[dep] for dep in calls['fit']['dependsOn']} == {'features'}

    names = ['features', 'fit', 'get', 'petal-area', 'sepal-area']
    assert all([
        calls[name]['containerOverrides']['command'] ==
        ['ploomber', 'task', name]
    ] for name in names)


def test_error_if_missing_boto3(monkeypatch, backup_packaged_project):

    exporter = batch.AWSBatchExporter('soopervisor.yaml', 'train')
    exporter.add()

    # simulate boto3 is not installed
    monkeypatch.setattr(util.importlib.util, 'find_spec', lambda _: None)

    with pytest.raises(ImportError) as excinfo:
        exporter.export()

    assert 'boto3 is required to use AWSBatchExporter' in str(excinfo.value)
