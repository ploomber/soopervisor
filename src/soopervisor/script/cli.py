from soopervisor.base.config import ScriptConfig
from soopervisor.argo.config import ArgoConfig
import click


# FIXME: is any of the tools still using this, if not, delete
@click.command()
@click.argument('command')
@click.option('--flavor',
              help='Which kind of schema to validate',
              default=None)
def _make_script(command, flavor):
    if flavor not in {None, 'argo'}:
        raise ValueError('flavor must be empty or "argo"')

    cls_ = ScriptConfig if not flavor else ArgoConfig
    script = cls_.from_project('.').to_script(command=command)
    print(script)
