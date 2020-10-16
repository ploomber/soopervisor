set -e

# initialize conda in the shell process
eval "$(conda shell.bash hook)"
conda activate base

# move to the project_root
cd {{config.paths.project}}

{% if config.cache_env %}
ENV_EXISTS=$(conda env list | grep "{{config.environment_prefix}}" | wc -l)
if [[ $ENV_EXISTS -ne 0 ]];
then
    echo "Environment exists, activating it..."
else
    echo "Environment does not exist, creating it..."
    conda env create --file {{config.paths.environment}} --prefix {{config.environment_prefix}}
fi
{% else %}
conda env create --file {{config.paths.environment}} --force --prefix {{config.environment_prefix}}
{% endif %}

echo 'Activating environtment...'
conda activate {{config.environment_prefix}}

# verify ploomber is installed
python -c "import ploomber" || PLOOMBER_INSTALLED=$?

if [[ $PLOOMBER_INSTALLED -ne 0 ]];
then
    echo "ploomber is not installed, consider adding it to your environment.yml file. Installing..."
    pip install ploomber
fi



if [ -f "setup.py" ]; then
    echo "Found setup.py, installing package..."
    pip install .
fi


# run pipeline
ploomber build {{config.args}}

{% if config.storage.enable %}
# ploomber ci should also be installed in the project's env
python -c "import soopervisor" || soopervisor_INSTALLED=$?
if [[ $soopervisor_INSTALLED -ne 0 ]];
then
    echo "soopervisor is not installed, consider adding it to your environment.yml file. Installing..."
    pip install soopervisor
fi

# upload products
soopervisor upload {{config.paths.products}}
{% endif %}
