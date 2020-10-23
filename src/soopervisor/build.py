from pathlib import Path

from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor import validate
from soopervisor.executors.LocalExecutor import LocalExecutor
from soopervisor.executors.DockerExecutor import DockerExecutor


def build_project(project_root, clean_products_path, dry_run):
    """
    Build a project using settings from a soopervisor.yaml file
    """
    config = ScriptConfig.from_path(project_root)

    print(f'Env prefix {config.environment_prefix}')
    print(config.paths)

    print(f'Output will be stored at: {config.storage.path}')

    validate.project(config)

    if clean_products_path:
        print('Cleaning product root folder...')
        config.clean_products()

    if config.executor == 'local':
        executor = LocalExecutor(script_config=config)
    elif config.executor == 'docker':
        executor = DockerExecutor(script_config=config)
    else:
        raise ValueError('Unknown executor "{}"'.format(config.executor))

    print('Running script with executor: {}'.format(repr(executor)))

    if dry_run:
        print('Dry run, skipping execution...')
        print(f'Script:\n{config.to_script()}')
    else:
        executor.execute()
        print('Successful build!')
