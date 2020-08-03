from pathlib import Path


def check_project(project_root):
    """
    Verify project has the right structure before running the script
    """

    if not Path(project_root, 'environment.yml').exists():
        raise FileNotFoundError('An "environment.yml" is required to declared '
                                'dependencies')

    if not Path(project_root, 'pipeline.yaml').exists():
        raise FileNotFoundError('An "pipeline.yaml" is required to declare '
                                'your pipeline')
