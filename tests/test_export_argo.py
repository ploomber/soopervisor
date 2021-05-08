import os
import subprocess
from pathlib import Path
from copy import copy

import yaml
import pytest
from argo.workflows.dsl import Workflow
from ploomber.spec import DAGSpec
from click.testing import CliRunner

from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor import cli


def test_argo_spec(tmp_sample_project):
    exporter = ArgoWorkflowsExporter(path_to_config='soopervisor.yaml',
                                     env_name='serve')
    d = exporter.add()

    run_task_template = d['spec']['templates'][0]
    tasks = d['spec']['templates'][1]['dag']['tasks']
    dag = DAGSpec('pipeline.yaml').to_dag()

    d['spec']['volumes'] = [{
        'name': 'nfs',
        'persistentVolumeClaim': {
            'claimName': 'nfs'
        }
    }]

    run_task_template['script']['volumeMounts'] = [{
        'name': 'nfs',
        'mountPath': '/mnt/nfs',
        'subPath': 'sample_project'
    }]

    # validate is a valig argo spec. NOTE: using copy because this modifies
    # the input dict
    assert Workflow.from_dict(copy(d))

    assert set(d) == {'apiVersion', 'kind', 'metadata', 'spec'}
    assert set(d['metadata']) == {'generateName'}
    assert set(d['spec']) == {'entrypoint', 'templates', 'volumes'}

    assert run_task_template['script']['image'] == 'continuumio/miniconda3'
    assert run_task_template['name'] == 'run-task'
    assert run_task_template['script']['workingDir'] == '/mnt/nfs'
    assert run_task_template['script']['volumeMounts'][0][
        'subPath'] == 'sample_project'

    assert d['metadata']['generateName'] == 'sample_project-'

    # check dependencies are set correctly
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


def test_custom_args(tmp_sample_project):
    Path('soopervisor.yaml').write_text('serve:\n    args: --some-arg')
    exporter = ArgoWorkflowsExporter(path_to_config='soopervisor.yaml',
                                     env_name='serve')
    spec = exporter.add()
    cmd = 'ploomber task {{inputs.parameters.task_name}} --force --some-arg'
    assert cmd in spec['spec']['templates'][0]['script']['source']


@pytest.mark.parametrize('config', [
    None,
    'args: --some-arg',
])
def test_argo_output_yaml(tmp_sample_project, config):
    if config:
        Path('soopervisor.yaml').write_text(config)

    exporter = ArgoWorkflowsExporter(path_to_config='soopervisor.yaml',
                                     env_name='serve')
    exporter.add()

    yaml_str = Path('serve', 'argo.yaml').read_text()
    # make sure the "source" key is represented in literal style
    # (https://yaml-multiline.info/) to make the generated script more readable
    assert 'source: |' in yaml_str


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
