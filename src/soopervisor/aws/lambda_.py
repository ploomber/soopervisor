"""
Online DAG deployment using AWS Lambda
"""
import ast
import shutil
import os
from pathlib import Path
import subprocess

from jinja2 import Environment, PackageLoader, StrictUndefined
from ploomber.util import default

from soopervisor import name_format

_env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                   undefined=StrictUndefined)
_env.filters['to_pascal_case'] = name_format.to_pascal_case


class ScriptExecutor:
    def __init__(self, debug=True):
        self._initial_working_directory = os.getcwd()
        self._names = []
        self._debug = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not self._debug:
            for name in self._names:
                name = Path(name)
                if name.exists():
                    name.unlink()

        os.chdir(self._initial_working_directory)

    def execute(self, name):
        self._names.append(name)
        content = _env.get_template(name).render()
        Path(name).write_text(content)
        subprocess.run(['bash', name], check=True)

    def copy_template(self, path, **render_kwargs):
        path = Path(path)

        path.parent.mkdir(exist_ok=True, parents=True)

        # self._names.append(path)
        content = _env.get_template(str(path)).render(**render_kwargs)
        path.write_text(content)

    def inline(self, *code):
        subprocess.run(code, check=True)

    def cd(self, dir_):
        path = Path(dir_)

        if not path.exists():
            path.mkdir(exist_ok=True, parents=True)

        os.chdir(dir_)

    def append(self, name, dst):
        # TODO: keep a copy of the original content to restore if needed
        content = _env.get_template(name).render()
        original = Path(dst).read_text()
        Path(dst).write_text(original + '\n' + content)

    def copy(self, src):
        # TODO should replace it if exists
        path = Path(src)

        if path.is_file():
            shutil.copy(src, path.name)
        else:
            shutil.copytree(src, path.name)

    def create_if_not_exists(self, name):
        if not Path(name).exists():
            content = _env.get_template(f'default/{name}').render()
            Path(name).write_text(content)
            self._names.append(name)


def warn_if_not_installed(name):
    if not shutil.which(name):
        print(f'It appears you don\'t have {name} CLI installed, you need it '
              'to execute "invoke aws-lambda build"')


def declares_name(path, name):
    m = ast.parse(Path(path).read_text())
    return name in [getattr(node, 'name', None) for node in m.body]


def main():
    if Path('aws-lambda').exists():
        raise FileExistsError('aws-lambda already exists, Rename or delete '
                              'to continue.')

    if declares_name('tasks.py', 'aws_lambda_build'):
        raise RuntimeError('tasks.py already has a "aws_lambda_build" '
                           'function. Rename or delete to continue.')

    print('Generating files to export to AWS Lambda...')
    # TODO: validate project structure: src/*/model.*, etc...
    pkg_name = default.find_package_name()

    # TODO: build is required to run this, perhaps use python setup.py bdist?
    # TODO: warn if deploying from a dirty commit, maybe ask for confirmation
    # and show the version?
    # TODO: support for OnlineDAG in app.py

    with ScriptExecutor() as e:
        e.create_if_not_exists('tasks.py')
        e.copy_template('aws-lambda/README.md')
        e.copy_template('aws-lambda/Dockerfile')
        e.copy_template('aws-lambda/app.py', package_name=pkg_name)
        e.copy_template('aws-lambda/template.yaml', package_name=pkg_name)
        e.copy_template('aws-lambda/test_aws_lambda.py')
        e.append('aws-lambda/tasks.py', 'tasks.py')
        e.cd('aws-lambda')

    print('Done. Files generated at aws-lambda/. '
          'See aws-lambda/README.md for details')
    print('Added build command: invoke aws-lambda-build')

    for name in ['docker', 'aws', 'sam']:
        warn_if_not_installed(name)
