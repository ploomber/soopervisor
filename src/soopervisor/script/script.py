"""
Command line interface

Steps:

1. Copy project_root to workspace
2. Look for a conda's environment.yml file, install dependencies (assume conda is installed)
3. Run `ploomber pipeline pipeline.yaml` (assume al output is saved in ./output)
4. Install this package
5. Upload 'output/ to box' (read credentials from ~/.box)

Notes:

Use jinja to generate the script (it makes easy to embed logic)
"""
from jinja2 import Environment, PackageLoader, StrictUndefined


def generate_script(config, command):
    """
    Generate a bash script (string) to run a pipeline in a clean environment

    Parameters
    ----------
    config : ScriptConfig
        Script settings
    command : str
        Command to execute. If None, runs "ploomber build"
    """
    env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                      undefined=StrictUndefined)
    template = env.get_template('script.sh')
    # config = __scape_spaces_on_paths(config)

    return template.render(config=config, command=command)


def __scape_spaces_on_paths(config):
    config["paths"]["environment"] = config["paths"]["environment"].replace(
        " ", "\ ")
    config["paths"]["products"] = config["paths"]["products"].replace(
        " ", "\ ")
    config["paths"]["project"] = config["paths"]["project"].replace(" ", "\ ")

    return config
