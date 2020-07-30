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


def generate_script(project_root, box=False):
    """
    Generate a bash script (string) to run a pipeline in a clean environment

    Parameters
    ----------
    project_root : str
        Path to the project root (the one that contains the pipeline.yaml file)
    box : str
        Whether to include the commad to upload products to box or not
    """
    # TODO: run pip install if there is a setup.py file
    env = Environment(loader=PackageLoader('ploomberci', 'assets'))
    template = env.get_template('script.sh')
    return template.render(project_root=project_root, box=box)
