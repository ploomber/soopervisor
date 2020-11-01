from ploomber.spec import DAGSpec
from soopervisor import export


def test_argo_spec(tmp_sample_project):
    d = export.to_argo('.')

    run_task_template = d['spec']['templates'][0]
    tasks = d['spec']['templates'][1]['dag']['tasks']
    dag = DAGSpec('pipeline.yaml').to_dag()

    assert run_task_template['name'] == 'run-task'
    assert run_task_template['script']['workingDir'] == '/mnt/vol'
    assert run_task_template['script']['volumeMounts'][0][
        'subPath'] == '/sample_project'

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
