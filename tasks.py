"""
Setup tasks (requires invoke: pip install invoke)
"""
import shutil
import sys
import platform
from pathlib import Path

from invoke import task

_DEFAULT_VERSION = '3.9'


@task
def setup(c, version=_DEFAULT_VERSION):
    """Configure development environment
    """
    suffix = '' if version == _DEFAULT_VERSION else version.replace('.', '-')
    name = f'soopervisor{suffix}'
    c.run(f'conda create --name {name} python={version} --yes')
    start = ('eval "$(conda shell.bash hook)" && '
             if platform.system() != 'Windows' else '')
    c.run(f'{start}'
          f'conda activate {name} '
          '&& pip install --editable .[dev]'
          '&& pip install --editable tests/assets/my_project')
    print(f'Done! Activate your environment with:\nconda activate {name}')


@task
def test(c, pty=True):
    """Run tests
    """
    # run tests except test_tutorials.py - that one needs extra config,
    # we're not running it as part of the CI
    c.run('pytest tests --ignore=tests/test_tutorials.py', pty=pty)


@task
def doc(c, open_=True):
    """Build docs
    """
    with c.cd('doc'):
        c.run('make html')
        if open_:
            c.run('open _build/html/index.html')


@task(aliases=['v'])
def version(c):
    """Release a new version
    """
    from pkgmt import versioneer
    versioneer.version(project_root='.', tag=True)


@task(aliases=['r'])
def release(c, tag, production=True):
    """Upload to PyPI
    """
    from pkgmt import versioneer
    versioneer.upload(tag, production=production)


@task
def doc_auto(c, port=8000):
    """Start hot reloading docs, the destination port can be passed as an
    argument
    """
    c.run(f'sphinx-autobuild doc doc/_build/html --port {port}')


@task
def install_git_hook(c, force=False):
    """Installs pre-push git hook
    """
    path = Path('.git/hooks/pre-push')
    hook_exists = path.is_file()

    if hook_exists:
        if force:
            path.unlink()
        else:
            sys.exit('Error: pre-push hook already exists. '
                     'Run: "invoke install-git-hook -f" to force overwrite.')

    shutil.copy('.githooks/pre-push', '.git/hooks')
    print(f'pre-push hook installed at {str(path)}')


@task
def uninstall_git_hook(c):
    """Uninstalls pre-push git hook
    """
    path = Path('.git/hooks/pre-push')
    hook_exists = path.is_file()

    if hook_exists:
        path.unlink()
        print(f'Deleted {str(path)}.')
    else:
        print('Hook doesn\'t exist, nothing to delete.')
