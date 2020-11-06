from soopervisor.script.ScriptConfig import ScriptConfig
import click


@click.command()
@click.argument('command')
def _make_script(command):
    # TODO: add option to switch ScriptConfig/ArgoConfig depending on use case
    # another option is to allow extra, then this can always be ScriptConfig
    script = ScriptConfig.from_path('.').to_script(validate=True,
                                                   command=command)
    print(script)
