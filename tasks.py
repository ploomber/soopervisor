"""
Setup tasks (requires invoke: pip install invoke)
"""
import versioneer
from invoke import task


@task
def setup(c, version='3.8'):
    """Configure development environment
    """
    suffix = '' if version == '3.8' else version.replace('.', '-')
    name = f'soopervisor{suffix}'
    c.run(f'conda create --name {name} python={version} --yes')
    c.run('eval "$(conda shell.bash hook)" '
          f'&& conda activate {name} '
          '&& pip install --editable .[dev]'
          '&& pip install --editable tests/assets/my_project')
    print(f'Done! Activate your environment with:\nconda activate {name}')


@task
def test(c):
    """Run all tests except the ones that use Docker
    """
    c.run('pytest tests', pty=True)


@task
def doc(c, open_=True):
    with c.cd('doc'):
        c.run('make html')
        if open_:
            c.run('open _build/html/index.html')


@task
def new(c):
    """Release a new version
    """
    versioneer.release(project_root='.', tag=True)


@task
def upload(c, tag, production=True):
    """Upload to PyPI
    """
    versioneer.upload(tag, production=production)


@task
def doc_auto(c):
    c.run('sphinx-autobuild doc doc/_build/html')
