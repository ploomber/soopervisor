"""
Setup tasks (requires invoke: pip install invoke)
"""
from invoke import task


@task
def setup(c):
    """Configure development environment
    """
    c.run('conda create --name soopervisor python=3.8 --yes')
    c.run('eval "$(conda shell.bash hook)" '
          '&& conda activate soopervisor '
          '&& pip install --editable .[dev]')
    print('Done! Activate your environment with:\nconda activate soopervisor')


@task
def test_no_docker(c):
    """Run all tests except the ones that use Docker
    """
    c.run('pytest tests --ignore tests/test_docker_executor.py', pty=True)
