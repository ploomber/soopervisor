"""
Online DAG deployment using AWS Lambda
"""
from ploomber.util import default
from ploomber.io._commander import Commander

from soopervisor.aws.util import warn_if_not_installed


def main(until=None):
    print('Generating files to export to AWS Lambda...')
    # TODO: validate project structure: src/*/model.*, etc...
    pkg_name = default.find_package_name()

    # TODO: build is required to run this, perhaps use python setup.py bdist?
    # TODO: warn if deploying from a dirty commit, maybe ask for confirmation
    # and show the version?
    # TODO: support for OnlineDAG in app.py

    with Commander(workspace='aws-lambda',
                   templates_path=('soopervisor', 'assets')) as e:
        e.create_if_not_exists('tasks.py')
        e.copy_template('aws-lambda/README.md')
        e.copy_template('aws-lambda/Dockerfile')

        e.copy_template('aws-lambda/test_aws_lambda.py')
        e.copy_template('aws-lambda/app.py', package_name=pkg_name)

        e.copy_template('aws-lambda/template.yaml', package_name=pkg_name)
        # ensure user has pytest
        e.run('pytest', 'aws-lambda', description='Testing')

        e.rm('dist', 'build')
        e.run('python', '-m', 'build', '--wheel', '.', description='Packaging')

        e.cp('dist', 'aws-lambda')
        e.cp('requirements.lock.txt', 'aws-lambda')

        e.cd('aws-lambda')
        e.run('sam', 'build', description='Building Docker image')

        if until == 'build':
            e.tw.write('Done. Run "docker images" to see your image.')
            return

        # TODO: guided only when the config  does not exist
        e.run('sam', 'deploy', '--guided', description='Deploying')

        e.tw.sep('=', 'Deployed to AWS Lambda', green=True)

    print('Done. Files generated at aws-lambda/. '
          'See aws-lambda/README.md for details')
    print('Added build command: invoke aws-lambda-build')

    for name in ['docker', 'aws', 'sam']:
        warn_if_not_installed(name)
