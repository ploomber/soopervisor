# exit if any command fails
set -e

# initialize conda in the shell process
eval "$(conda shell.bash hook)"
conda activate base

# move to the project_root
cd {{paths.project}}

# install the env, the user might name it differently so we force it to be
# installed as "ploomber-env"
conda env create --file {{paths.environment}} --name ploomber-env --force
conda activate ploomber-env

# verify ploomber is installed
python -c "import ploomber" || PLOOMBER_INSTALLED=$?

if [ $PLOOMBER_INSTALLED -ne 0 ];
then
    echo "ploomber is not installed, consider adding it to your environment.yml file. Installing..."
    pip install ploomber
fi



if [ -f "setup.py" ]; then
    echo "Found setup.py, installing package..."
    pip install .
fi


# run pipeline
ploomber build

{% if storage.enable %}
# ploomber ci should also be installed in the project's env
python -c "import soopervisor" || soopervisor_INSTALLED=$?
if [ $soopervisor_INSTALLED -ne 0 ];
then
    echo "soopervisor is not installed, consider adding it to your environment.yml file. Installing..."
    pip install git+https://github.com/ploomber/ci-for-ds
fi

# upload products
soopervisor upload {{paths.products}}
{% endif %}
