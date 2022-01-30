from pathlib import Path
from unittest.mock import Mock, ANY
import yaml
import pytest
from ploomber.io import _commander, _commander_tester
from soopervisor.kubeflow.export import KubeflowExporter, commons


def _mock_docker_calls(monkeypatch, cmd):
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
def mock_docker_calls(monkeypatch):
    path = str(Path('src', 'my_project', 'pipeline.yaml'))
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           f'DAGSpec("{path}").to_dag().clients)')
    tester = _mock_docker_calls(monkeypatch, cmd)
    yield tester


@pytest.fixture
def mock_docker_calls_serve(monkeypatch):
    path = str(Path('src', 'my_project', 'pipeline.serve.yaml'))
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           f'DAGSpec("{path}").to_dag().clients)')
    tester = _mock_docker_calls(monkeypatch, cmd)
    yield tester


@pytest.fixture
def mock_docker_calls_callables(monkeypatch):
    cmd = ('from ploomber.spec import '
           'DAGSpec; print("File" in '
           'DAGSpec("pipeline.yaml").to_dag().clients)')
    yield _mock_docker_calls(monkeypatch, cmd, 'callables')


# Test the task output is same as it's product
@pytest.mark.parametrize('mode, args', [
    ['incremental', ''],
    ['regular', ''],
    ['force', ' --force'],
],
                         ids=['incremental', 'regular', 'force'])
def test_export(monkeypatch, mock_docker_calls, backup_packaged_project,
                no_sys_modules_cache, skip_repo_validation, mode, args):
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)

    exporter = KubeflowExporter.new(path_to_config='soopervisor.yaml',
                                    env_name='serve')

    exporter.add()
    exporter.export(mode=mode, until=None)

    yaml_str = Path('serve/ploomber_pipeline.yaml').read_text()
    spec = yaml.safe_load(yaml_str)
    # dag = DAGSpec.find().to_dag()

    load_tasks_mock.assert_called_once_with(cmdr=ANY, name='serve', mode=mode)

    # print(yaml_str)
    total_dag_size = len(spec['spec']['templates'])

    # Get dag by pipeline name
    dag = [
        template['dag'] for template in spec['spec']['templates']
        if 'my-project' in template['name']
    ][0]
    tasks = dag['tasks']

    get_task = [
        template for template in spec['spec']['templates']
        if 'get' in template['name']
    ][0]

    cmd = ('ploomber task get --entry-point ' +
           str(Path('src', 'my_project', 'pipeline.yaml')))

    assert total_dag_size - 1 == len(tasks)
    assert set(spec) == {'apiVersion', 'kind', 'metadata', 'spec'}
    assert 'generateName' in set(spec['metadata'])
    assert {'entrypoint', 'templates'}.issubset(set(spec['spec']))

    container_cmd = get_task['container']['command'][2]
    assert cmd in container_cmd
    if args:
        assert args in container_cmd
    assert get_task['container']['image'] == 'image_target:0.1dev'
    assert spec['metadata']['generateName'] == 'my-project-'
