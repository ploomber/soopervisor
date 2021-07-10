import click

from pathlib import Path


def check_lock_files_exist():
    if not Path('environment.lock.yml').exists() and not Path(
            'requirements.lock.txt').exists():
        raise click.ClickException("""
Expected requirements.txt.lock or environment.lock.yml at the root directory, \
add one and try again.

pip: pip freeze > requirements.txt.lock
conda: conda env export --no-build --file environment.lock.yml
""")
