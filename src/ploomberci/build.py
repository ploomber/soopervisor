from pathlib import Path

from ploomberci.script.ScriptConfig import ScriptConfig
from ploomberci.executors.LocalExecutor import LocalExecutor


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


def build_project(project, clean_products_path):
    """
    Build a project using settings from a ploomberci.yaml file
    """
    print('Building project')

    config = ScriptConfig.from_path(project)

    check_project(config)

    # FIXME: should config or executor take care of saving?
    script = config.save_script()

    if clean_products_path:
        print('Cleaning product root folder...')
        config.clean_products()

    print('Generated script:\n', script)

    print('Running script...')

    executor = LocalExecutor(project_root=config.paths.project,
                             product_root=config.paths.products,
                             script=script)
    executor.execute()

    print('Successful build!')
