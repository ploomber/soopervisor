import json
from pathlib import Path
import subprocess

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


def test_add(backup_packaged_project):
    lambda_.add(name='serve')

    assert Path('serve', 'Dockerfile').exists()
    assert Path('serve', 'app.py').exists()
    assert Path('serve', 'README.md').exists()
    assert Path('serve', 'template.yaml').exists()
    assert Path('serve', 'test_aws_lambda.py').exists()


def test_submit(backup_packaged_project):
    subprocess.run(['ploomber', 'build'], check=True)
    subprocess.run(
        ['cp', 'products/model.pickle', 'src/my_project/model.pickle'],
        check=True)
    lambda_.add(name='serve')
    erase_lines('serve/app.py', from_=14, to=15)
    erase_lines('serve/test_aws_lambda.py', from_=10, to=12)
    replace_line('serve/test_aws_lambda.py',
                 line=15,
                 value=f'    body = {json.dumps(body)}')

    lambda_.main(name='serve')
