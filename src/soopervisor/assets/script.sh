set -e

# initialize conda in the shell process
eval "$(conda shell.bash hook)"
conda activate base


ENV_EXISTS=$(conda env list | grep "{{project_name}}" | wc -l)
if [[ $ENV_EXISTS -ne 0 ]];
then
    echo "Environment exists, activating it..."
else
    echo "Environment does not exist, creating it..."
    conda env create --file 'environment.lock.yml' --name {{project_name}}
fi

echo 'Activating environtment...'
conda activate {{project_name}}

# verify ploomber is installed
python -c "import ploomber" || PLOOMBER_INSTALLED=$?

if [[ $PLOOMBER_INSTALLED -ne 0 ]];
then
    echo "ploomber is not installed. Installing..."
    pip install ploomber
fi

if [ -f "setup.py" ]; then
    echo "Found setup.py, installing package..."
    pip install .
fi

{% if command -%}
echo 'Executing task...'
{{command}}

{% else -%}
echo 'Executing pipeline...'
ploomber build
{% endif -%}

echo 'Done!'
