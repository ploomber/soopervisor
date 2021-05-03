import os
from unittest.mock import Mock, MagicMock
import json
from pathlib import Path
import subprocess

import pytest
import moto
import boto3

from soopervisor.aws import batch
from ploomber.io import _commander

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

    batch_client.create_job_queue(jobQueueName='some_job_queue',
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


class CommanderTester:
    def __init__(self, run=None, return_value=None):
        self._run = run or []
        self._return_value = return_value or dict()

    def __call__(self, cmd):
        if cmd in self._run:
            return subprocess.check_call(cmd)
        elif cmd in self._return_value:
            return self._return_value[cmd]


def test_submit_to_aws_batch(mock_batch, monkeypatch, backup_packaged_project):
    cmd = 'from ploomber.spec import DAGSpec; print("File" in DAGSpec.find().to_dag().clients)'
    tester = CommanderTester(
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

    batch.main()

    jobs = mock_batch.list_jobs(jobQueue='some_job_queue')['jobSummaryList']

    jobs_info = mock_batch.describe_jobs(jobs=[job['jobId']
                                               for job in jobs])['jobs']

    # moto currently ignores some of the parameters
    boto3_mock.submit_job.call_args_list


def test_package_project(monkeypatch, backup_packaged_project):
    def run(cmd):
        # from IPython import embed
        # embed()
        if cmd == ('docker', 'build', '.', '--tag', 'my_project:0.1dev'):
            pass
        elif cmd == ('docker', 'run', 'my_project:0.1dev', 'ploomber',
                     'status'):
            raise subprocess.CalledProcessError(2, 'cmd')
        else:
            return subprocess.check_call(cmd)

    # commander = MagicMock()
    # commander.__enter__.return_value = commander
    # commander.run.side_effect = run
    # Commander = Mock(return_value=commander)
    # monkeypatch.setattr(batch, 'Commander', Commander)

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = run
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)

    batch.main()
