import tarfile
import os.path
import shutil
from pathlib import Path
from itertools import chain
from glob import iglob
import subprocess


def git_tracked_files():
    out = subprocess.check_output(
        ['git', 'ls-tree', '-r', 'HEAD', '--name-only'])
    return out.decode().splitlines()


def glob_all(path):
    hidden = iglob(str(Path(path) / '**' / '.*'), recursive=True)
    normal = iglob(str(Path(path) / '**'), recursive=True)
    return chain(hidden, normal)


def copy(src, dst, include=None):
    tracked = git_tracked_files()
    include = set() if include is None else set(include)

    for f in glob_all(path=src):
        if (f not in tracked
                and f not in include) or Path(f).name == '.gitignore':
            print(f'Ignoring {f}')
        else:
            target = Path(dst, f)
            target.parent.mkdir(exist_ok=True, parents=True)
            print(f'Copying {f} -> {target}')
            shutil.copy(f, dst=target)


def compress_dir(src, dst):
    with tarfile.open(dst, "w:gz") as tar:
        tar.add(src, arcname=os.path.basename(src))

    shutil.rmtree(src)
