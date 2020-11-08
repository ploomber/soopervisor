from ploomber.spec import DAGSpec
from soopervisor.argo.config import ArgoConfig
from soopervisor.argo import export


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
