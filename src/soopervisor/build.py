from pathlib import Path

from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def check_project(config):
    """
    Verify project has the right structure before running the script
    """
    if not Path(config.paths.environment).exists():
        raise FileNotFoundError(
            'An environment file was expected at: {}'.format(
                config.paths.environment))

    if not Path(config.paths.project, 'pipeline.yaml').exists():
        raise FileNotFoundError('A "pipeline.yaml" is required to declare '
                                'your pipeline')


def build_project(project_root, clean_products_path):
    """
    Build a project using settings from a soopervisor.yaml file
    """
    print('Building project')

    config = ScriptConfig.from_path(project_root)

    check_project(config)

    if clean_products_path:
        print('Cleaning product root folder...')
        config.clean_products()

    print('Running script...')

    executor = LocalExecutor(script_config=config)
    executor.execute()

    print('Successful build!')
