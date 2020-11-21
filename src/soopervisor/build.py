from soopervisor.base.config import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def build_project(project_root, clean_products_path, dry_run, load_dag=True):
    """
    Build a project using settings from a soopervisor.yaml file
    """
    config = ScriptConfig.from_project(project_root, load_dag=load_dag)

    print(f'Env prefix {config.environment_prefix}')
    print(config.paths)

    if config.storage.provider:
        # TODO: better message depending on box/local
        print(
            f'Upon execution, output will be copied to: {config.storage.path}')

    if clean_products_path:
        print('Cleaning product root folder...')
        config.clean_products()

    if config.executor == 'local':
        executor = LocalExecutor(script_config=config)
    elif config.executor == 'docker':
        # this imports docker, do so only when you're actually going to use it
        from soopervisor.executors.DockerExecutor import DockerExecutor
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
