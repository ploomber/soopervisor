"""
Setup tasks (requires invoke: pip install invoke)
"""
import platform
import versioneer
from invoke import task

_DEFAULT_VERSION = '3.9'


@task
def setup(c, version=_DEFAULT_VERSION):
    """Configure development environment
    """
    suffix = '' if version == _DEFAULT_VERSION else version.replace('.', '-')
    name = f'soopervisor{suffix}'
    c.run(f'conda create --name {name} python={version} --yes')
    c.run('eval "$(conda shell.bash hook)" && '
          if platform.system() != 'Windows' else ''
          f'conda activate {name} '
          '&& pip install --editable .[dev]'
          '&& pip install --editable tests/assets/my_project')
    print(f'Done! Activate your environment with:\nconda activate {name}')


@task
def test(c):
    """Run tests
    """
    c.run('pytest tests', pty=True)


@task
def doc(c, open_=True):
    """Build docs
    """
    with c.cd('doc'):
        c.run('make html')
        if open_:
            c.run('open _build/html/index.html')


@task
def new(c):
    """Release a new version
    """
    versioneer.version(project_root='.', tag=True)


@task
def upload(c, tag, production=True):
    """Upload to PyPI
    """
    versioneer.upload(tag, production=production)


@task
def doc_auto(c):
    """Start hot reloading docs
    """
    c.run('sphinx-autobuild doc doc/_build/html')
