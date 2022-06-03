import click

from pathlib import Path


def _all_locks_present(prefix, suffix, lock='lock'):
    matched_files = [
        path.stem for path in list(Path('.').glob(f"{prefix}.*.{suffix}"))
    ]
    task_names = [
        s for file in matched_files for s in file.split(".")
        if s not in (prefix, lock)
    ]
    return 2 * len(set(task_names)) == len(task_names)


def check_lock_files_exist():
    if not Path('environment.lock.yml').exists() and not Path(
            'requirements.lock.txt').exists():
        raise click.ClickException("""
Expected requirements.lock.txt or environment.lock.yml at the root directory, \
add one and try again.

pip: pip freeze > requirements.lock.txt
conda: conda env export --no-build --file environment.lock.yml
""")

    if not (_all_locks_present('requirements', 'txt')
            and _all_locks_present('environment', 'yml')):
        raise click.ClickException("""
        Expected requirements.<task-name>.lock.txt file for \
        each requirements.<task-name>.txt file OR \
        environment.<task-name>.lock.yml for each \
        environment.<task-name>.yml file at the root directory.
        Add relevant lock files and try again.

        """)
