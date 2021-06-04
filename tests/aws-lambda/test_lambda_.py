import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest
import yaml
from click import ClickException

from soopervisor.aws.lambda_ import AWSLambdaExporter
from ploomber.io import _commander, _commander_tester

body = {
    "sepal length (cm)": 5.1,
    "sepal width (cm)": 3.5,
    "petal length (cm)": 1.4,
    "petal width (cm)": 0.2
}


def _edit_generated_files():
    _erase_lines('serve/app.py', from_=14, to=16)
    _erase_lines('serve/test_aws_lambda.py', from_=10, to=12)
    _replace_line('serve/test_aws_lambda.py',
                  line=15,
                  value=f'    body = {json.dumps(body)}')


def _erase_lines(path, from_, to):
    lines = Path(path).read_text().splitlines()

    for idx in range(from_ - 1, to):
        lines[idx] = ''

    Path(path).write_text('\n'.join(lines))


def _replace_line(path, line, value):
    path = Path(path)
    lines = path.read_text().splitlines()
    lines[line - 1] = value
    path.write_text('\n'.join(lines))


def test_add(backup_packaged_project):
    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')
    exporter.add()

    with open('soopervisor.yaml') as f:
        d = yaml.safe_load(f)

    assert d['serve'] == {'backend': 'aws-lambda'}

    assert Path('serve', 'Dockerfile').exists()
    assert Path('serve', 'app.py').exists()
    assert Path('serve', 'README.md').exists()
    assert Path('serve', 'template.yaml').exists()
    assert Path('serve', 'test_aws_lambda.py').exists()


@pytest.fixture
def mock_sam_calls(monkeypatch):
    tester = _commander_tester.CommanderTester(run=[
        ('python', '-m', 'build', '--wheel', '.'),
    ])
    subprocess_mock = Mock()
    subprocess_mock.check_call.side_effect = tester
    subprocess_mock.check_output.side_effect = tester
    monkeypatch.setattr(_commander, 'subprocess', subprocess_mock)
    return tester


def test_export(backup_packaged_project, mock_sam_calls):
    Path('requirements.lock.txt').touch()
    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)

    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')
    exporter.add()
    _edit_generated_files()
    exporter.export(mode=None, until=None, skip_tests=False)

    assert mock_sam_calls.calls == [
        ('pytest', 'serve'),
        ('python', '-m', 'build', '--wheel', '.'),
        ('sam', 'build'),
        ('sam', 'deploy', '--guided'),
    ]


def test_export_non_packaged_project(tmp_sample_project):
    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')

    with pytest.raises(ClickException) as excinfo:
        exporter.add()

    expected = ('AWS Lambda is only supported in packaged projects.'
                ' See the documentation for an example.')
    assert expected == str(excinfo.value)


def test_skip_tests(backup_packaged_project, mock_sam_calls):
    Path('requirements.lock.txt').touch()
    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)

    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')
    exporter.add()
    _edit_generated_files()
    exporter.export(mode=None, until=None, skip_tests=True)

    assert mock_sam_calls.calls == [
        ('python', '-m', 'build', '--wheel', '.'),
        ('sam', 'build'),
        ('sam', 'deploy', '--guided'),
    ]


def test_generate_reqs_lock_txt_from_env_lock_yml(backup_packaged_project,
                                                  mock_sam_calls, capsys):

    Path('environment.lock.yml').write_text("""
dependencies:
  - python=3.8
  - pip
  - pip:
    - a
    - b
""")

    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)

    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')
    exporter.add()
    _edit_generated_files()

    exporter.export(mode=None, until=None, skip_tests=False)

    captured = capsys.readouterr()
    assert 'Missing requirements.lock.txt file.' in captured.out
    assert not Path('requirements.lock.txt').exists()


def test_error_when_missing_env_yml_and_reqs_txt(backup_packaged_project,
                                                 monkeypatch):
    Path('environment.lock.yml').unlink()

    with pytest.raises(ClickException) as excinfo:
        AWSLambdaExporter('soopervisor.yaml', 'serve')

    msg = ('Expected environment.lock.yml or requirements.txt.lock at the '
           'root directory. Add one.')
    assert msg == str(excinfo.value)
