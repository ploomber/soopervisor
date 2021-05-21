import json
from pathlib import Path
import subprocess

import pytest
import yaml
from click.testing import CliRunner
from click import ClickException
from soopervisor import cli

from soopervisor.aws.lambda_ import AWSLambdaExporter
from ploomber.io import _commander

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


class PassCall:
    def __init__(self, *args):
        self.args = args
        self.called = False

    def __call__(self, cmd):
        if cmd == self.args:
            self.called = True
        else:
            return subprocess.run(cmd, check=True)


def test_export(backup_packaged_project, monkeypatch):
    # mock call to: sam deploy --guided
    pass_call = PassCall('sam', 'deploy', '--guided')
    monkeypatch.setattr(_commander.subprocess, 'check_call', pass_call)

    Path('requirements.lock.txt').touch()
    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)

    exporter = AWSLambdaExporter('soopervisor.yaml', 'serve')
    exporter.add()
    _edit_generated_files()
    runner = CliRunner()

    result = runner.invoke(cli.export, ['serve'], catch_exceptions=False)

    assert pass_call.called
    assert result.exit_code == 0


def test_generate_reqs_lock_txt_from_env_lock_yml(backup_packaged_project,
                                                  monkeypatch, capsys):
    # mock call to: sam deploy --guided
    pass_call = PassCall('sam', 'deploy', '--guided')
    monkeypatch.setattr(_commander.subprocess, 'check_call', pass_call)

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

    exporter.export()
    # TODO: mock lambda calls that builds docker image

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
