# Local example

This tutorial runs a pipeline in a local Kubernetes cluster using `k3d`.

## Pre-requisites


* [docker](https://docs.docker.com/get-docker/)

## Building Docker image

We provide a Docker image so you can quickly run this example:

```bash
# get repository
git clone https://github.com/ploomber/soopervisor
cd soopervisor/tutorials/kubernetes

# create a directory to store the pipeline output
export SHARED_DIR=$HOME/ploomber-k8s
mkdir -p $SHARED_DIR

# build image
docker build --tag ploomber-k8s .

# start
docker run -i -t \
    --privileged=true -v /var/run/docker.sock:/var/run/docker.sock \
    --volume $SHARED_DIR:/mnt/shared-folder \
    --env SHARED_DIR \
    --env PLOOMBER_STATS_ENABLED=false \
    -p 2746:2746 \
    ploomber-k8s /bin/bash
```

**NOTE**: We need to run `docker run` in privileged mode since we’ll be running
`docker` commands inside the container.
[More on that here](https://www.docker.com/blog/docker-can-now-run-within-docker/)

## Create Kubernetes cluster

The Docker image comes with `k3d` pre-installed; let’s create a cluster:

```bash
# create cluster
k3d cluster create mycluster --volume $SHARED_DIR:/host --port 2746:2746

# check cluster
kubectl get nodes
```

**NOTE**: If you see the error message
`Bind for 0.0.0.0:2746 failed: port is already allocated`, you may
drop the `--port 2746:2746` and try again:
`k3d cluster create mycluster --volume $SHARED_DIR:/host` the command
will work but you’ll be unable to open Argo’s GUI.

## Install Argo

We now install argo; note that we are using a custom installation file
(`argo-pns.yaml`) to ensure this works with `k3d`.

```bash
# install argo
kubectl create ns argo
kubectl apply -n argo -f argo-pns.yaml

# check argo pods (once they're all running, argo is ready)
kubectl get pods -n argo
```

**NOTE**: `argo-pns.yaml` is a custom file that changes the Argo executor to PNS;
this is required to ensure Argo works on `k3d`; however, this change
isn’t required in a production environment.

## Get sample Ploomber pipeline

```bash
# get example
ploomber examples -n templates/ml-intermediate -o ml-intermediate
cd ml-intermediate

# configure development environment
cp requirements.txt requirements.lock.txt
pip install ploomber soopervisor
pip install -r requirements.txt
```

## Configure target platform

Soopervisor allows you to configure the target platform using a
`soopervisor.yaml` file, let’s add it and set the backend to
`argo-worflows`:

```bash
soopervisor add training --backend argo-workflows
```

Usually, you’d manually edit `soopervisor.yaml` to configure your
environment; for this example, let’s use one that we
[already configured](https://github.com/ploomber/soopervisor/blob/master/tutorials/kubernetes/soopervisor-k8s.yaml),
which tells soopervisor to mount a local directory to every pod so we can review results later:

```bash
cp ../soopervisor-k8s.yaml soopervisor.yaml
```

We must configure the project to store all outputs in the shared folder, so we
copy the [pre-configured file](https://github.com/ploomber/soopervisor/blob/master/tutorials/kubernetes/env-k8s.yaml):

```bash
cp ../env-k8s.yaml env.yaml
```

## Submit pipeline

We finished configuring; let’s now submit the workflow:

```bash
# build docker image (takes a few minutes the first time) and generate an argo's yaml spec
soopervisor export training --skip-tests --ignore-git

# import image to the k8s cluster
k3d image import ml-intermediate:latest --cluster mycluster

# submit workflow
argo submit -n argo --watch training/argo.yaml
```

**Congratulations! You just ran Ploomber on Kubernetes! 🎉**

**NOTE**: You may fail to submit pipeline with a different example (e.g. `ml-basic`). That is because we used the `ml-intermediate` pipeline as the example, which already has parametrized products. Therefore, we need to add the `env.yaml` and parameterize the pipeline to run it successfully.

However, the `ml-basic` pipeline was not parametrized. Thus we need to parameterize it first. Please refer to [this documentation](https://docs.ploomber.io/en/latest/user-guide/parametrized.html) for more information on parametrized pipelines.

**NOTE**: `k3d image import` is only required if creating the cluster with `k3d`.

Once the execution finishes, take a look at the generated artifacts:

```sh
ls /mnt/shared-folder
```

## Incremental builds

Try exporting the pipeline again:

```bash
soopervisor export training --skip-tests --ignore-git
```

You’ll see a message like this: `Loaded DAG in 'incremental' mode has no tasks to submit`.
Soopervisor checks the status of your pipeline and only schedules tasks that have changed
since the last run; since all your tasks are the same, there is nothing to run!

Let’s now modify one of the tasks and submit it again:

```bash
# modify the fit.py task, add a print statement
echo -e "\nprint('Hello from Kubernetes')" >> fit.py

# re-build docker image and submit
soopervisor export training --skip-tests --ignore-git
k3d image import ml-intermediate:latest --cluster mycluster
argo submit -n argo --watch training/argo.yaml
```

You’ll see that this time, only the `fit` task ran because that’s the only
tasks whose source code change, we call this incremental builds, and they’re a
a great feature for quickly running experiments in your pipeline, such as changing
model hyperparameters or adding new pre-processing methods; it saves a lot of
time since you don’t have to execute the entire pipeline every time.

## Clean up

To delete the cluster:

```bash
k3d cluster delete mycluster
```
