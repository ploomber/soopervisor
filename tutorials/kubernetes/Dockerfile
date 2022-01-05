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

# install ploomber and soopervisor
RUN pip install ploomber soopervisor

# copy example and install dependencies
RUN ploomber examples -n templates/ml-intermediate -o mli
RUN pip install -r mli/requirements.txt

# copy argo installer with pns executor
COPY argo-pns.yaml argo-pns.yaml

# copy pre-configured soopervisor and env files
COPY soopervisor-k8s.yaml soopervisor-k8s.yaml
COPY env-k8s.yaml env-k8s.yaml

