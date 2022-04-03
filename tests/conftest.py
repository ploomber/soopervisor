import importlib
import tempfile
import sys
import subprocess
from faker import Faker
import os
import shutil
from pathlib import Path
from copy import copy
from unittest.mock import Mock, MagicMock
import posthog
import json

import my_project
import pytest
import moto
import boto3

from ploomber.io import _commander, _commander_tester

from soopervisor import commons


class CustomCommander(_commander.Commander):
    """
    A subclass of Commander that ignores calls to
    CustomCommander.run('docker', ...)
    """
    def run(self, *args, **kwargs):
        if args[0] == 'docker':
            print(f'ignoring: {args} {kwargs}')
        else:
            return super().run(*args, **kwargs)


def git_init():
    """Creates an empty git repository and commits
    """
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'config', 'user.email', 'ci@ploomberio'])
    subprocess.check_call(['git', 'config', 'user.name', 'Ploomber'])
    subprocess.check_call(['git', 'add', '--all'])
    subprocess.check_call(['git', 'commit', '-m', 'commit'])


def _mock_commander_calls(monkeypatch, cmd, proj, tag):
    """
    Mock subprocess calls made by ploomber.io._commander.Commander (which
    is used interally by the soopervisor.commons.docker module).

    This allows us to prevent actual CLI calls to "docker run". Instead, we
    mock the call and return a value. However, this function will allow calls
    to "python -m build --sdist" to pass. For details, see the CommanderTester
    docstring in the ploomber package.
    """
    tester = _commander_tester.CommanderTester(
        run=[
            ('python', '-m', 'build', '--sdist'),
        ],
        return_value={
            ('docker', 'run', f'{proj}:{tag}', 'python', '-c', cmd): b'True\n'
        })

    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)

    return tester


def _path_to_tests():
    """Returns absolute path to the tests/ directory
    """
    return Path(__file__).absolute().parent


@pytest.fixture(scope='class')
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope='class', autouse=True)
def external_access(monkeypatch_session):
    external_access = MagicMock()
    external_access.get_something = MagicMock(return_value='Mock was used.')
    monkeypatch_session.setattr(posthog, 'capture',
                                external_access.get_something)


@pytest.fixture
def root_path():
    """Returns absolute path to the root directory
    """
    return _path_to_tests().parent


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture
def tmp_empty(tmp_path):
    """Creates a temporary empty folder and moves to it
    """
    old = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(Path(tmp_path).resolve())
    os.chdir(old)


@pytest.fixture
def tmp_sample_project(tmp_path):
    relative_path_project = "assets/sample_project"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    sample_project = _path_to_tests() / relative_path_project
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    os.chdir(old)


@pytest.fixture
def tmp_fast_pipeline(tmp_path):
    relative_path_project = "assets/fast-pipeline"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    fast_pipeline = _path_to_tests() / relative_path_project
    shutil.copytree(str(fast_pipeline), str(tmp))

    os.chdir(str(tmp))
    Path('environment.yml').touch()

    yield tmp

    os.chdir(old)


@pytest.fixture
def backup_packaged_project():
    old = os.getcwd()

    backup = tempfile.mkdtemp()
    root = Path(my_project.__file__).parents[2]

    # sanity check, in case we change the structure
    assert root.name == 'my_project'

    shutil.copytree(str(root), str(Path(backup, 'my_project')))

    pkg_root = str(
        Path(importlib.util.find_spec('my_project').origin).parents[2])
    os.chdir(str(pkg_root))

    yield

    os.chdir(old)

    shutil.rmtree(str(root))
    shutil.copytree(str(Path(backup, 'my_project')), str(root))
    shutil.rmtree(backup)


@pytest.fixture
def tmp_sample_project_in_subdir(tmp_sample_project):
    """
    Sample as tmp_sample_project but moves all contents to a subdirectory
    """
    files = os.listdir()
    sub_dir = Path('subdir')
    sub_dir.mkdir()

    for f in files:
        Path(f).rename(sub_dir / f)

    yield tmp_sample_project


@pytest.fixture
def tmp_callables(tmp_path):
    """Pipeline with PythonCallable tasks
    """
    relative_path = "assets/callables"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path)
    sample_project = _path_to_tests() / relative_path
    shutil.copytree(str(sample_project), str(tmp))

    os.chdir(str(tmp))

    yield tmp

    os.chdir(old)


@pytest.fixture
def session_sample_project(tmp_path_factory):
    """
    Similar to tmp_directory but tasks should not modify content, since
    it's a session-wide fixture
    """
    sample_project = str(_path_to_tests() / 'assets' / 'sample_project')
    tmp_dir = tmp_path_factory.mktemp('session-wide-tmp-directory')
    tmp_target = str(tmp_dir / 'sample_project')

    shutil.copytree(sample_project, tmp_target)
    old = os.getcwd()
    os.chdir(tmp_target)

    yield tmp_target

    # TODO: check files were not modified

    os.chdir(old)


@pytest.fixture(scope='session')
def download_projects(tmpdir_factory):
    tmp_path = tmpdir_factory.mktemp('projects')
    subprocess.run([
        'git',
        'clone',
        'https://github.com/ploomber/projects',
        str(tmp_path),
    ],
                   check=True)
    yield str(Path(tmp_path).resolve())


@pytest.fixture
def tmp_projects(download_projects, tmp_path):
    old = os.getcwd()
    target = tmp_path / 'projects'
    shutil.copytree(download_projects, target)
    os.chdir(str(target))
    yield str(Path(target).resolve())
    os.chdir(old)


@pytest.fixture
def tmp_lazy_load(download_projects, tmp_path):
    relative_path_project = "assets/lazy-load"
    old = os.getcwd()
    tmp = Path(tmp_path, relative_path_project)
    fast_pipeline = _path_to_tests() / relative_path_project
    shutil.copytree(str(fast_pipeline), str(tmp))

    os.chdir(str(tmp))
    Path('requirements.lock.txt').touch()

    yield tmp

    os.chdir(old)


@pytest.fixture
def no_sys_modules_cache():
    """
    Removes modules from sys.modules that didn't exist before the test
    """
    mods = set(sys.modules)

    yield

    current = set(sys.modules)

    to_remove = current - mods

    for a_module in to_remove:
        del sys.modules[a_module]


@pytest.fixture
def add_current_to_sys_path():
    old = copy(sys.path)
    sys.path.insert(0, os.path.abspath('.'))
    yield sys.path
    sys.path = old


@pytest.fixture
def skip_repo_validation(monkeypatch):
    # do not validate repository (using the default value will raise an error)
    monkeypatch.setattr(commons.docker, '_validate_repository', lambda x: x)


# AWS BATCH

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


@pytest.fixture
def monkeypatch_docker_client(monkeypatch):
    """
    We're using an old moto version because newer ones are not working
    (https://github.com/spulec/moto/issues/1793). The version we're using
    (1.3.14) calls docker.from_env but since GitHub macOS machines don't
    have docker installed and installing it takes too long, we mock the call

    https://github.com/actions/virtual-environments/issues/17
    https://github.com/marketplace/actions/setup-docker - this takes too long
    """
    monkeypatch.setattr(moto.batch.models.docker, 'from_env', Mock())


@pytest.fixture
def mock_docker_sample_project(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_commander_calls(monkeypatch, cmd, 'sample_project', 'latest')


@pytest.fixture
def mock_docker_my_project_serve(monkeypatch):
    path = str(Path('src', 'my_project', 'pipeline.serve.yaml'))
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           f'DAGSpec("{path}").to_dag().clients)')
    tester = _mock_commander_calls(monkeypatch, cmd, 'my_project', '0.1dev')
    yield tester


@pytest.fixture
def mock_docker_my_project(monkeypatch):
    path = str(Path('src', 'my_project', 'pipeline.yaml'))
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           f'DAGSpec("{path}").to_dag().clients)')
    tester = _mock_commander_calls(monkeypatch, cmd, 'my_project', '0.1dev')
    yield tester


@pytest.fixture
def mock_docker_sample_project_serve(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.serve.yaml").to_dag().clients)')
    yield _mock_commander_calls(monkeypatch, cmd, 'sample_project', 'latest')
