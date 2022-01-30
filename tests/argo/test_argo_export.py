import os
import subprocess
from pathlib import Path
from copy import copy
from unittest.mock import Mock, ANY

import yaml
import pytest
from argo.workflows.dsl import Workflow
from ploomber.spec import DAGSpec
from click.testing import CliRunner

from conftest import _mock_docker_calls
from soopervisor.argo.export import ArgoWorkflowsExporter, commons
from soopervisor import cli


@pytest.fixture
def mock_docker_calls(monkeypatch):
    path = str(Path('src', 'my_project', 'pipeline.yaml'))
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           f'DAGSpec("{path}").to_dag().clients)')
    tester = _mock_docker_calls(monkeypatch, cmd, 'my_project', '0.1dev')
    yield tester


@pytest.mark.parametrize('mode, args', [
    ['incremental', ''],
    ['regular', ''],
    ['force', ' --force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_export(mock_docker_calls, backup_packaged_project, monkeypatch, mode,
                args, skip_repo_validation):
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = ArgoWorkflowsExporter.new(path_to_config='soopervisor.yaml',
                                         env_name='serve')
    exporter.add()
    exporter.export(mode=mode, until=None)

    yaml_str = Path('serve/argo.yaml').read_text()
    spec = yaml.safe_load(yaml_str)
    dag = DAGSpec.find().to_dag()

    load_tasks_mock.assert_called_once_with(cmdr=ANY, name='serve', mode=mode)

    # make sure the "source" key is represented in literal style
    # (https://yaml-multiline.info/) to make the generated script more readable
    assert 'source: |' in yaml_str

    run_task_template = spec['spec']['templates'][0]
    tasks = spec['spec']['templates'][1]['dag']['tasks']

    cmd = ('ploomber task {{inputs.parameters.task_name}} --entry-point ' +
           str(Path('src', 'my_project', 'pipeline.yaml')))
    assert run_task_template['script']['source'] == cmd + args

    assert spec['spec']['volumes'] == []
    assert run_task_template['script']['volumeMounts'] == []
    assert Workflow.from_dict(copy(spec))
    assert set(spec) == {'apiVersion', 'kind', 'metadata', 'spec'}
    assert set(spec['metadata']) == {'generateName'}
    assert set(spec['spec']) == {'entrypoint', 'templates', 'volumes'}

    # should not change workingdir
    assert run_task_template['script']['workingDir'] is None

    assert run_task_template['script']['image'] == 'image_target:0.1dev'
    assert run_task_template['name'] == 'run-task'
    assert spec['metadata']['generateName'] == 'my-project-'
    assert all([
        set(dag[t['name']].upstream) == set(t['dependencies']) for t in tasks
    ])

    # tasks call the right template
    assert set(t['template'] for t in tasks) == {'run-task'}

    # check each task uses the right parameters
    assert all([
        t['arguments']['parameters'][0] == {
            'name': 'task_name',
            'value': t['name']
        } for t in tasks
    ])


def test_custom_volumes(mock_docker_calls, backup_packaged_project,
                        skip_repo_validation):
    exporter = ArgoWorkflowsExporter.new(path_to_config='soopervisor.yaml',
                                         env_name='serve')
    exporter.add()

    spec = yaml.safe_load(Path('soopervisor.yaml').read_text())
    spec['serve']['mounted_volumes'] = [{
        'name': 'nfs',
        'sub_path': 'some_subpath',
        'spec': {
            'persistentVolumeClaim': {
                'claimName': 'someName'
            }
        }
    }]

    Path('soopervisor.yaml').write_text(yaml.safe_dump(spec))

    # reload exporter
    ArgoWorkflowsExporter.load(path_to_config='soopervisor.yaml',
                               env_name='serve').export(mode='incremental',
                                                        until=None)

    spec = yaml.safe_load(Path('serve/argo.yaml').read_text())

    assert spec['spec']['volumes'] == [{
        'name': 'nfs',
        'persistentVolumeClaim': {
            'claimName': 'someName'
        }
    }]

    run_task_template = spec['spec']['templates'][0]
    assert run_task_template['script']['volumeMounts'] == [{
        'name':
        'nfs',
        'mountPath':
        '/mnt/nfs',
        'subPath':
        'some_subpath'
    }]


def test_export_with_null_repository(mock_docker_calls,
                                     backup_packaged_project,
                                     skip_repo_validation, capsys):
    exporter = ArgoWorkflowsExporter.new(path_to_config='soopervisor.yaml',
                                         env_name='serve')
    exporter.add()

    # set empty repository
    spec = yaml.safe_load(Path('soopervisor.yaml').read_text())
    spec['serve']['repository'] = None
    Path('soopervisor.yaml').write_text(yaml.safe_dump(spec))

    # reload exporter
    ArgoWorkflowsExporter.load(path_to_config='soopervisor.yaml',
                               env_name='serve').export(mode='incremental',
                                                        until=None)

    spec = yaml.safe_load(Path('serve/argo.yaml').read_text())

    script = spec['spec']['templates'][0]['script']

    assert script['imagePullPolicy'] == 'Never'

    captured = capsys.readouterr()
    assert 'null repository found in soopervisor.yaml' in captured.out


# move to project's CI
@pytest.mark.skip
@pytest.mark.parametrize(
    'name',
    [
        'ml-intermediate',
        'etl',
        'ml-online',
    ],
)
def test_generate_valid_argo_specs(name, tmp_projects):
    if name == 'ml-online':
        subprocess.run(['pip', 'uninstall', 'ml-online', '--yes'], check=True)
        subprocess.run(['pip', 'install', 'ml-online/'], check=True)

    os.chdir(name)

    runner = CliRunner()
    result = runner.invoke(
        cli.add,
        ['serve', '--backend', 'argo-workflows'],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    # validate argo workflow
    content = Path('serve', 'argo.yaml').read_text()
    assert Workflow.from_dict(yaml.safe_load(content))
