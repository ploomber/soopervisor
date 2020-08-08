from pathlib import Path

from ploomberci.script.ScriptConfig import ScriptConfig
from ploomberci.executors.LocalExecutor import LocalExecutor


def check_project(project_root):
    """
    Verify project has the right structure before running the script
    """

    if not Path(project_root, 'environment.yml').exists():
        raise FileNotFoundError('An "environment.yml" is required to declare '
                                'dependencies')

    if not Path(project_root, 'pipeline.yaml').exists():
        raise FileNotFoundError('A "pipeline.yaml" is required to declare '
                                'your pipeline')


def build_project(project_root):
    """
    Build a project using settings from a ploomberci.yaml file
    """
    print('Building project')

    check_project(project_root)

    config = ScriptConfig.from_path(project_root)
    # FIXME: should config or executor take care of saving?
    script = config.save_script()

    print('Generated script:\n', script)

    print('Running script...')

    executor = LocalExecutor(project_root=config.project_root,
                             product_root=config.product_root,
                             script=script)
    executor.execute()

    print('Successful build!')
