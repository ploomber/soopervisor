# Dockerfile to build an image with docker, kubectl, k3d, and airflow
FROM continuumio/miniconda3:latest

RUN apt-get update
RUN apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release --yes

RUN apt-get install vim --yes

# install docker
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update

RUN apt-get install docker-ce docker-ce-cli containerd.io --yes

# install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# install k3d
RUN curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | bash

# install ploomber and soopervisor
RUN pip install ploomber soopervisor

# copy example and install dependencies
RUN ploomber examples -n templates/ml-intermediate -o mli
RUN pip install -r mli/requirements.txt

# install airflow and extra dependencies
RUN pip install apache-airflow
RUN pip install apache-airflow-providers-cncf-kubernetes

# configure airlow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
RUN airflow db init

RUN airflow users create \
    --username ploomber \
    --firstname Peter \
    --lastname Parker \
    --role Admin \
    --email spiderman@superhero.org \
    --password ploomber


# copy pre-configured soopervisor and env files
COPY soopervisor-airflow.yaml soopervisor-airflow.yaml
COPY env-airflow.yaml env-airflow.yaml

# copy pipeline with overriden pull policy
COPY ml-intermediate.py ml-intermediate.py

COPY start_airflow.sh start_airflow.sh
