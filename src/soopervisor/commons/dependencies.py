import click

from pathlib import Path
from collections import defaultdict

DEFAULT_IMAGE_NAME = 'default'


def _no_missing_dependencies(prefix, suffix):
    tasks = get_task_dependency_files(prefix, suffix)
    if len(tasks) > 1:
        # If multiple dependency file present, every
        # requirements.task-__.txt/ environment.task-__.yml file
        # should have a corresponding requirements.task-__.lock.txt/
        # environment.-__.lock.yml file
        for task_pattern, paths in tasks.items():
            if 'dependency' not in paths or 'lock' not in paths:
                return False
    return len(tasks) > 0


def get_task_dependency_files(prefix, suffix, lock='lock'):
    """
    Return all requirements/ environment files
    for each task in the below dict format:
    {
      task_name : { 'dependency' : path,
                 'lock': path of lock file
               }
    }
    task_name is 'default' for requirements.txt / environment.yml

    Parameters
    ----------

    prefix : str
        requirements / environment

    suffix : str
        txt / yml

    """
    task_files = defaultdict(dict)
    matched_files = [
        path.name for path in list(Path('.').glob(f"{prefix}*.{suffix}"))
    ]
    for filename in matched_files:
        task_name = [
            s for s in filename.split(".") if s not in (prefix, lock, suffix)
        ]
        task_name = DEFAULT_IMAGE_NAME if not task_name else task_name[
            0].replace('__', '*')
        if lock in filename:
            task_files[task_name]['lock'] = filename
        else:
            task_files[task_name]['dependency'] = filename
    return task_files


def get_default_image_key():
    return DEFAULT_IMAGE_NAME


def check_lock_files_exist():
    if not Path('environment.lock.yml').exists() and not Path(
            'requirements.lock.txt').exists():
        raise click.ClickException("""
Expected requirements.lock.txt or environment.lock.yml at the root directory, \
add one and try again.

pip: pip freeze > requirements.lock.txt
conda: conda env export --no-build --file environment.lock.yml
""")

    if not (_no_missing_dependencies('requirements', 'txt')
            or _no_missing_dependencies('environment', 'yml')):
        raise click.ClickException("""
        Expected requirements.<task-name>.lock.txt file for \
        each requirements.<task-name>.txt file OR \
        environment.<task-name>.lock.yml for each \
        environment.<task-name>.yml file at the root directory.
        Add relevant files and try again.

        """)
