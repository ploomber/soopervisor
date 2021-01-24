from pathlib import Path
from copy import copy

from ploomber.spec import DAGSpec
from soopervisor.argo.config import ArgoConfig
from soopervisor.argo import export

from argo.workflows.dsl import Workflow


def test_argo_spec(tmp_sample_project):
    d = export.project(ArgoConfig.from_project(project_root='.'))

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


def test_argo_output_yaml(tmp_sample_project):
    export.project(ArgoConfig.from_project(project_root='.'))
    yaml_str = Path('argo.yaml').read_text()
    # make sure the "source" key is represented in literal style
    # (https://yaml-multiline.info/) to make the generated script more readable
    assert 'source: |' in yaml_str
