# FIXME: this is almost copy of tutorials/kubernetes/Dockerfile, we should
# publish the image and then change the FROM directive to avoid this redundancy

# Dockerfile to build an image with docker, kubectl, k3d, and argo's cli
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

# argo cli
RUN curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.2.6/argo-linux-amd64.gz
RUN gunzip argo-linux-amd64.gz
RUN chmod +x argo-linux-amd64
RUN mv ./argo-linux-amd64 /usr/local/bin/argo
RUN argo version

RUN pip install ploomber soopervisor soorgeon
RUN pip install jupyterlab

# copy argo installer with pns executor
COPY argo-pns.yaml argo-pns.yaml

# END OF COPY FROM  tutorials/kubernetes/Dockerfile

# copy pre-configured soopervisor file
COPY soopervisor-workflow.yaml soopervisor-workflow.yaml

# get sample notebook
RUN wget https://raw.githubusercontent.com/ploomber/ci-notebooks/master/titanic-logistic-regression-with-python/nb.py
RUN jupytext nb.py --to ipynb
RUN rm -f nb.py

# dependencies
RUN conda install pygraphviz -c conda-forge -y
COPY requirements.lock.txt requirements.lock.txt
RUN pip install -r requirements.lock.txt

# data
COPY test.csv test.csv
COPY train.csv train.csv

COPY start.sh start.sh
CMD bash start.sh
