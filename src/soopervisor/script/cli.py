from soopervisor.base.config import ScriptConfig
import click


@click.command()
@click.argument('command')
def _make_script(command):
    # TODO: add option to switch ScriptConfig/ArgoConfig depending on use case
    # another option is to allow extra, then this can always be ScriptConfig
    script = ScriptConfig.from_project('.').to_script(command=command)
    print(script)
