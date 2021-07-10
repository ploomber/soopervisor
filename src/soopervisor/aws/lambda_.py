"""
Online DAG deployment using AWS Lambda
"""
from pathlib import Path
from ploomber.util import default
from ploomber.io._commander import Commander

from click.exceptions import ClickException

from soopervisor.aws.util import warn_if_not_installed
from soopervisor.aws.config import AWSLambdaConfig
from soopervisor.commons.conda import generate_reqs_txt_from_env_yml
from soopervisor import commons
from soopervisor import abc


class AWSLambdaExporter(abc.AbstractExporter):
    CONFIG_CLASS = AWSLambdaConfig

    def export(self, mode=None, until=None, skip_tests=False):
        if mode is not None:
            raise ValueError("AWS Lambda does not support 'mode'")

        return self._export(cfg=self._cfg,
                            env_name=self._env_name,
                            until=until,
                            skip_tests=skip_tests)

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @staticmethod
    def _add(cfg, env_name):
        try:
            pkg_name = default.find_package_name()
        except ValueError as e:
            raise ClickException(
                'AWS Lambda is only supported in packaged projects. '
                'See the documentation for an example.') from e

        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('aws-lambda/README.md')
            e.copy_template('aws-lambda/Dockerfile')

            e.copy_template('aws-lambda/test_aws_lambda.py',
                            package_name=pkg_name)
            e.copy_template('aws-lambda/app.py', package_name=pkg_name)

            e.copy_template('aws-lambda/template.yaml', package_name=pkg_name)
            e.success('Done.')
            e.print(
                'Next steps:\n1. Add an input example to '
                f'{env_name}/test_aws_lambda.py\n'
                f'2. Add the input parsing logic to {env_name}/app.py\n'
                f'3. Submit to AWS Lambda with: soopervisor export {env_name}')

            # TODO: use e.warn_on_exit
            for name in ['docker', 'aws', 'sam']:
                warn_if_not_installed(name)

    @staticmethod
    def _export(cfg, env_name, until, skip_tests):

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

            commons.dependencies.check_lock_files_exist()

            if not Path('requirements.lock.txt').exists() and Path(
                    'environment.lock.yml').exists():
                e.warn_on_exit(
                    'Missing requirements.lock.txt file. '
                    'Once was created from the pip '
                    'section in the environment.lock.yml file but this '
                    'may not work if there are missing dependencies. Add '
                    'one or ensure environment.lock.yml includes all pip '
                    'dependencies.')

                generate_reqs_txt_from_env_yml('environment.lock.yml',
                                               output='requirements.lock.txt')
                e.rm_on_exit('requirements.lock.txt')

            e.cp('requirements.lock.txt')

            # TODO: ensure user has pytest before running
            if not skip_tests:
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
