import click

from pathlib import Path
from collections import defaultdict


def _no_missing_dependencies(prefix, suffix):
    tasks = get_task_dependency_files(prefix, suffix)
    # Every requirements.*.txt file should have a corresponding
    # requirements.*.lock.txt file
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
        task_name = 'default' if not task_name else task_name[0]
        if lock in filename:
            task_files[task_name]['lock'] = filename
        else:
            task_files[task_name]['dependency'] = filename
    return task_files


def check_lock_files_exist():
    if not Path('environment.lock.yml').exists() and not Path(
            'requirements.lock.txt').exists():
        raise click.ClickException("""
Expected requirements.lock.txt or environment.lock.yml at the root directory, \
add one and try again.

pip: pip freeze > requirements.lock.txt
conda: conda env export --no-build --file environment.lock.yml
""")

    if not _no_missing_dependencies('requirements', 'txt') \
            and not _no_missing_dependencies('environment', 'yml'):
        raise click.ClickException("""
        Expected requirements.<task-name>.lock.txt file for \
        each requirements.<task-name>.txt file OR \
        environment.<task-name>.lock.yml for each \
        environment.<task-name>.yml file at the root directory.
        Add relevant files and try again.

        """)
