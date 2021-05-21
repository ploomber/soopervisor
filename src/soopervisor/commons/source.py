import tarfile
import os.path
import shutil
from pathlib import Path
from itertools import chain
from glob import iglob
import subprocess

from click.exceptions import ClickException


def git_tracked_files():
    res = subprocess.run(['git', 'ls-tree', '-r', 'HEAD', '--name-only'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    if not res.returncode:
        return res.stdout.decode().splitlines()
    else:
        raise ClickException(
            'Could not obtain git tracked files. Non-packaged projects'
            ' must be in a git repository, create one with "git init".'
            f' Error message: {res.stderr.decode()}')


def glob_all(path):
    hidden = iglob(str(Path(path) / '**' / '.*'), recursive=True)
    normal = iglob(str(Path(path) / '**'), recursive=True)
    return chain(hidden, normal)


def copy(src, dst, include=None):
    # TODO: warn if git is dirty (new files wont be included)

    tracked = git_tracked_files()
    include = set() if include is None else set(include)

    for f in glob_all(path=src):
        if (f not in tracked
                and f not in include) or Path(f).name == '.gitignore':
            print(f'ignoring {f}')
        else:
            target = Path(dst, f)
            target.parent.mkdir(exist_ok=True, parents=True)
            print(f'copying {f} -> {target}')
            shutil.copy(f, dst=target)


def compress_dir(src, dst):
    with tarfile.open(dst, "w:gz") as tar:
        tar.add(src, arcname=os.path.basename(src))

    shutil.rmtree(src)
