conda create --name airflow python=3.8 --yes
conda activate airflow

# source:
# https://airflow.apache.org/docs/apache-airflow/stable/start/local.html


export AIRFLOW_HOME=~/airflow

AIRFLOW_VERSION=2.0.1
PYTHON_VERSION=3.8
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

airflow db init

rm $AIRFLOW_HOME/airflow.cfg
cp airflow.cfg $AIRFLOW_HOME/airflow.cfg

airflow users create \
    --username admin \
    --firstname Name \
    --lastname Lastname \
    --role Admin \
    --email user@example.com


pip install soopervisor honcho
