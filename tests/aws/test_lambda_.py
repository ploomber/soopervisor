import json
from pathlib import Path
import subprocess

import pytest

from soopervisor.aws import lambda_

body = {
    "sepal length (cm)": 5.1,
    "sepal width (cm)": 3.5,
    "petal length (cm)": 1.4,
    "petal width (cm)": 0.2
}


def erase_lines(path, from_, to):
    lines = Path(path).read_text().splitlines()

    for idx in range(from_ - 1, to):
        lines[idx] = ''

    Path(path).write_text('\n'.join(lines))


def replace_line(path, line, value):
    path = Path(path)
    lines = path.read_text().splitlines()
    lines[line - 1] = value
    path.write_text('\n'.join(lines))


@pytest.fixture
def setup_my_project(tmp_packaged_project):
    subprocess.run(['pip', 'install', '--editable', '.'], check=True)

    yield

    subprocess.run(['pip', 'uninstall', 'my_project', '--yes'], check=True)


def test_package_project(setup_my_project):

    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)

    lambda_.main()

    erase_lines('aws-lambda/app.py', from_=14, to=15)

    erase_lines('aws-lambda/test_aws_lambda.py', from_=10, to=12)
    replace_line('aws-lambda/test_aws_lambda.py',
                 line=15,
                 value=f'    body = {json.dumps(body)}')

    subprocess.run(['invoke', 'aws-lambda-build'], check=True)
