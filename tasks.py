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
          '&& pip install --editable .[all]')
    print('Done! Activate your environment with:\nconda activate soopervisor')
