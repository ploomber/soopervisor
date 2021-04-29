"""
Online DAG deployment using AWS Lambda
"""
from pathlib import Path

from ploomber.util import default

from soopervisor.aws.util import (declares_name, ScriptExecutor,
                                  warn_if_not_installed)


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
