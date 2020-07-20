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
from jinja2 import Template

template = Template("""
# exit if any command fails
set -e

# initialize conda in the shell process
eval "$(conda shell.bash hook)"
conda activate base

# move to the project_root
cd {{project_root}}

# install the env, the user might name it differently so we force it to be
# installed as "ploomber-env"
conda env create --file environment.yml --name ploomber-env --force
conda activate ploomber-env

# run pipeline
ploomber entry pipeline.yaml

{% if box %}
# command to upload a folder to box...
ploomberci 
{% endif %}

""")


def generate_script(project_root, workspace):
    """"
    Generate a bash script (string) to run a pipeline in a clean environment

    Parameters
    ----------
    project_root : str
        Path to the project root (the one that contains the pipeline.yaml file)
    workspace : str
        A folder to use for executing the pipeline
    """"
    # User should be able to configure behavior with a ploomber-ci.yaml file
    config = Path(project_root, 'ploomber-ci.yaml')
    # read config...

    # example ploomber-ci.yaml
    """
    box: true
    """


    return template.render(project_root=project_root, box=config['box'])