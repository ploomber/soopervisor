"""
Online DAG deployment using AWS Lambda
"""
from pathlib import Path
from ploomber.util import default
from ploomber.io._commander import Commander

from soopervisor.aws.util import warn_if_not_installed
from soopervisor.aws.config import AWSLambdaConfig
from soopervisor import abc


class AWSLambdaExporter(abc.AbstractExporter):
    CONFIG_CLASS = AWSLambdaConfig

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @staticmethod
    def _add(cfg, env_name):
        pkg_name = default.find_package_name()

        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('aws-lambda/README.md')
            e.copy_template('aws-lambda/Dockerfile')

            e.copy_template('aws-lambda/test_aws_lambda.py',
                            package_name=pkg_name)
            e.copy_template('aws-lambda/app.py', package_name=pkg_name)

            e.copy_template('aws-lambda/template.yaml', package_name=pkg_name)

            e.append('aws-lambda/soopervisor.yaml',
                     'soopervisor.yaml',
                     env_name=env_name)
            e.success('Done.')
            e.print(
                'Next steps:\n1. Add an input example to '
                f'{env_name}/test_aws_lambda.py\n'
                f'2. Add the input parsing logic to {env_name}/app.py\n'
                f'3. Submit to AWS Lambda with: soopervisor export {env_name}')

            for name in ['docker', 'aws', 'sam']:
                warn_if_not_installed(name)

    @staticmethod
    def _submit(cfg, env_name, until):

        # TODO: validate project structure: src/*/model.*, etc...

        # TODO: build is required to run this, perhaps use python setup.py
        # bdist?
        # TODO: warn if deploying from a dirty commit, maybe ask for
        # confirmation
        # and show the version?
        # TODO: support for OnlineDAG in app.py
        # TODO: check if OnlineModel can be initialized from the package

        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.cp('requirements.lock.txt')

            # TODO: ensure user has pytest
            e.run('pytest', env_name, description='Testing')

            e.rm('dist', 'build')
            e.run('python',
                  '-m',
                  'build',
                  '--wheel',
                  '.',
                  description='Packaging')
            e.cp('dist')

            e.cd(env_name)

            # TODO: template.yaml with version number

            e.run('sam', 'build', description='Building Docker image')

            if until == 'build':
                e.tw.write(
                    'Done.\nRun "docker images" to see your image.'
                    '\nRun "sam local start-api" to test your API locally')
                return

            args = ['sam', 'deploy']

            if Path('samconfig.toml').exists():
                e.warn('samconfig.toml already exists. Skipping '
                       'guided deployment...')
            else:
                args.append('--guided')
                e.info('Starting guided deployment...')

            e.run(*args, description='Deploying')

            e.success('Deployed to AWS Lambda')
