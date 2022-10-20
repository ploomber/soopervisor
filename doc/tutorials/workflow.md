# Full workflow

```{important}
This tutorial requires soopervisor `0.6.2` or higher, and soorgeon `0.0.10` or higher.
```


This tutorial shows how to go from a monolithic Jupyter notebook to a
modular, production-ready pipeline deployed in workflow by using the tools
in our ecosystem:

1. [soorgeon](https://github.com/ploomber/soorgeon)
2. [ploomber](https://github.com/ploomber/ploomber)
3. [soopervisor](https://github.com/ploomber/soopervisor)

## Pre-requisites


* [docker](https://docs.docker.com/get-docker/)

## Building Docker image

We provide a Docker image so you can quickly run this example:

```bash
# get repository
git clone https://github.com/ploomber/soopervisor
cd soopervisor/tutorials/workflow

# build image
docker build --tag ploomber-workflow .

# create a directory to store the pipeline output
export SHARED_DIR=$HOME/ploomber-workflow
rm -rf $SHARED_DIR
mkdir -p $SHARED_DIR

# start (takes ~1 minute to be ready)
docker run -i -t \
    --privileged=true -v /var/run/docker.sock:/var/run/docker.sock \
    --volume $SHARED_DIR:/mnt/shared-folder \
    --env SHARED_DIR \
    --env PLOOMBER_STATS_ENABLED=false \
    --network host \
    ploomber-workflow
```

```{note}
**NOTE**: We need to run `docker run` in privileged mode since we’ll be running
`docker` commands inside the container.
[More on that here.](https://www.docker.com/blog/docker-can-now-run-within-docker/)
```

Upon initialization, JupyterLab will be running at [http://127.0.0.1:8888](http://127.0.0.1:8888)

## Refactor notebook

First, we use `soorgeon` to refactor the notebook:

```bash
soorgeon refactor nb.ipynb -p /mnt/project/output -d parquet
```

We can generate a plot to visualize the dependencies:

```bash
ploomber plot
```

If you open the generated `pipeline.png`, you’ll see that `soorgeon`
inferred the dependencies among the sections in the notebook and built a
Ploomber pipeline automatically!

Now you can iterate this modular pipeline with Ploomber, but for now, let’s
go to the next stage and deploy to Kubernetes.

## Configure target platform

Soopervisor allows you to configure the target platform using a
`soopervisor.yaml` file, let’s add it and set the backend to
`argo-worflows`:

```bash
# soopervisor add requires a requirements.lock.txt file
cp requirements.txt requirements.lock.txt

# add the taget environment
soopervisor add training --backend argo-workflows
```

Usually, you’d manually edit `soopervisor.yaml` to configure your
environment; for this example, let’s use one that we
[already configured](https://github.com/ploomber/soopervisor/blob/master/tutorials/workflow/soopervisor-workflow.yaml),
which tells soopervisor to mount a local directory to every pod so we can review results later:

```bash
cp /soopervisor-workflow.yaml soopervisor.yaml
```

## Submit pipeline

We finished configuring; let’s now submit the workflow:

```bash
# build docker image and generate an argo's yaml spec
soopervisor export training --skip-tests --ignore-git --mode force

# import image to the k8s cluster
k3d image import project:latest --cluster mycluster

# submit workflow
argo submit -n argo --watch training/argo.yaml
```

**Congratulations! You just went from a legacy notebook to production-ready pipeline! 🎉**

```{note}
`k3d image import` is only required if creating the cluster with `k3d`.
```

Once the execution finishes, take a look at the generated artifacts:

```sh
ls /mnt/project
```

````{tip}
You may also watch the progress from the UI.

```sh
# port forwarding to enable the UI
kubectl -n argo port-forward --address 0.0.0.0 svc/argo-server 2746:2746
```

Then, open: https://127.0.0.1:2746
````

## Clean up

To delete the cluster:

```bash
k3d cluster delete mycluster
```
