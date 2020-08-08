# exit if any command fails
set -e

# initialize conda in the shell process
eval "$(conda shell.bash hook)"
conda activate base

# move to the project_root
cd {{project_root}}

# install the env, the user might name it differently so we force it to be
# installed as "ploomber-env"
conda env create --file {{path_to_environment}} --name ploomber-env --force
conda activate ploomber-env

# run pipeline
ploomber build

{% if box.enable %}
# command to upload a folder to box...
ploomberci 
{% endif %}
