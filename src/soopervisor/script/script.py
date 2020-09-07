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
from jinja2 import Environment, PackageLoader


def generate_script(config):
    """
    Generate a bash script (string) to run a pipeline in a clean environment

    Parameters
    ----------
    project_root : str
        Path to the project root (the one that contains the pipeline.yaml file)
    config : ScriptConfig
        Script settings
    """
    env = Environment(loader=PackageLoader('soopervisor', 'assets'))
    template = env.get_template('script.sh')
    d = __scape_spaces_on_paths(config.dict())

    return template.render(**d)


def __scape_spaces_on_paths(config):
    config["paths"]["environment"] = config["paths"]["environment"].replace(" ", "\ ")
    config["paths"]["products"] = config["paths"]["products"].replace(" ", "\ ")
    config["paths"]["project"] = config["paths"]["project"].replace(" ", "\ ")

    return config
