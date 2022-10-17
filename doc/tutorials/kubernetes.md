# Kubernetes (Argo)

```{note}
**Got questions?** Reach out to us on [Slack](https://ploomber.io/community/).
```

This tutorial shows how to run a pipeline in Kubernetes
via [Argo Workflows](https://argoproj.github.io/workflows) locally or in Google Cloud.

If you encounter any issues with this
tutorial, [let us know](https://github.com/ploomber/soopervisor/issues/new?title=Argo%20Workflows%20tutorial%20problem).

[Click here to see the Argo Community Meeting talk](https://youtu.be/FnpXyg-5W_c).

We have two tutorials:
* [Local](#local-example) (only requires `docker`)
* [Google Cloud](#google-cloud)

## Local example

```{tip}
This tutorial requires soopervisor `0.6.1` or higher
```

This tutorial runs a pipeline in a local Kubernetes cluster using `k3d`.

### Pre-requisites


* [docker](https://docs.docker.com/get-docker/)

### Building Docker image

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

```{note}
We need to run `docker run` in privileged mode since we’ll be running
`docker` commands inside the container.
[More on that here](https://www.docker.com/blog/docker-can-now-run-within-docker/)
```

### Create Kubernetes cluster

The Docker image comes with `k3d` pre-installed; let’s create a cluster:

```bash
# create cluster
k3d cluster create mycluster --volume $SHARED_DIR:/host --port 2746:2746

# check cluster
kubectl get nodes
```

```{note}
If you see the error message
`Bind for 0.0.0.0:2746 failed: port is already allocated`, you may
drop the `--port 2746:2746` and try again:
`k3d cluster create mycluster --volume $SHARED_DIR:/host` the command
will work but you’ll be unable to open Argo’s GUI.
```

### Install Argo

We now install argo; note that we are using a custom installation file
(`argo-pns.yaml`) to ensure this works with `k3d`.

```bash
# install argo
kubectl create ns argo
kubectl apply -n argo -f argo-pns.yaml

# check argo pods (once they're all running, argo is ready)
kubectl get pods -n argo
```

```{note}
`argo-pns.yaml` is a custom file that changes the Argo executor to PNS;
this is required to ensure Argo works on `k3d`; however, this change
isn’t required in a production environment.
```

````{tip}
Optionally, submit sample Argo workflow to ensure everything is working:
```sh
argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml
```
````

### Get sample Ploomber pipeline

```bash
# get example
ploomber examples -n templates/ml-intermediate -o ml-intermediate
cd ml-intermediate

# configure development environment
cp requirements.txt requirements.lock.txt
pip install ploomber soopervisor
pip install -r requirements.txt
```

### Configure target platform

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

### Submit pipeline

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

```{note}
You may fail to submit pipeline with a different example (e.g. `ml-basic`). That is because we used the `ml-intermediate` pipeline as the example, which already has parametrized products. Therefore, we need to add the `env.yaml` and parameterize the pipeline to run it successfully.

However, the `ml-basic` pipeline was not parametrized. Thus we need to parameterize it first. Please refer to [this documentation](https://docs.ploomber.io/en/latest/user-guide/parametrized.html) for more information on parametrized pipelines.
```

```{note}
`k3d image import` is only required if creating the cluster with `k3d`.
```

Once the execution finishes, take a look at the generated artifacts:

```sh
ls /mnt/shared-folder
```

````{tip}
You may also watch the progress from the UI.

  ```sh
  # port forwarding to enable the UI
  kubectl -n argo port-forward svc/argo-server 2746:2746
  ```
  Then, open: https://127.0.0.1:2746
````

### Incremental builds

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

### Clean up

To delete the cluster:

```bash
k3d cluster delete mycluster
```

## Google Cloud

```{tip}
This tutorial requires soopervisor `0.6.1` or higher
```

This second tutorial runs a pipeline in a local Kubernetes cluster using Google Cloud.

```{note}
You may use or create a new [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) to follow this tutorial.
```

### Pre-requisites


* `kubectl`
* [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
* [conda instructions](https://docs.conda.io/en/latest/miniconda.html)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* Install Ploomber with `pip install ploomber`

### Instructions

Create a cluster and install Argo:

```sh
# create cluster
gcloud container clusters create my-cluster --num-nodes=1 --zone us-east1-b

# install argo
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/stable/manifests/quick-start-postgres.yaml

# create storage bucket (choose whatever name you want)
gsutil mb gs://YOUR-BUCKET-NAME
```

Submit a sample workflow to make sure Argo is working:

```sh
argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/hello-world.yaml
```

````{tip}
  Enable Argo’s UI:

  ```sh
  # port forwarding to enable the UI
  kubectl -n argo port-forward svc/argo-server 2746:2746
  ```
  Then, open: https://127.0.0.1:2746
````

Install `ploomber`:

```sh
pip install ploomber
```

Let’s now run a Ploomber sample Machine Learning pipeline:

```sh
# get example
ploomber examples -n templates/ml-online -o ml-online
cd ml-online

# configure development environment
ploomber install

# activate environment
conda activate ml-online

# add a new target platform
soopervisor add training --backend argo-workflows
```

The previous command creates a `soopervisor.yaml` file where we can configure
the container registry to upload our Docker image:

```yaml
training:
  backend: argo-workflows
  repository: gcr.io/PROJECT-ID/my-ploomber-pipeline
```

Replace `PROJECT-ID` with your actual project ID.

Each task will run in isolation, we must ensure that products generated by
a given task are available to its corresponding downstream tasks. Ww can use
Google Cloud Storage for that, add the following to the
`src/ml_online/pipeline.yaml` file:

```yaml
# more content above...

serializer: ml_online.io.serialize
unserializer: ml_online.io.unserialize

# add these two lines
clients:
  File: ml_online.clients.get_gcloud

# content continues...
```

The previous change tells Ploomber to call the function `get_gcloud` defined
in module `src/ml_online/clients.py` to get the client. Edit the
`clients.py` to add your bucket name:

```python
from ploomber.clients import GCloudStorageClient

def get_gcloud():
    # edit YOUR-BUCKET-NAME
    return GCloudStorageClient(bucket_name='YOUR-BUCKET-NAME',
                               parent='ml-online',
                               json_credentials_path='credentials.json')
```

You can ignore the rest of the file. Finally, we add service account credentials to
upload to Google Cloud Storage. To learn more about service accounts,
[click here](https://cloud.google.com/docs/authentication/production).

Store the service account details in a `credentials.json` in the root project
directory (same folder as `setup.py`):

We are ready to execute the workflow:

```sh
# authenticate to push docker image
gcloud auth configure-docker

# packages code, create docker image and upload it (takes a few mins)
soopervisor export training

# submit workflow
argo submit -n argo training/argo.yaml
```

You may keep track of execution by opening the UI. Check out the bucket to see output.

**Congratulations! You just ran Ploomber on Kubernetes!**

```{note}
You may fail to submit pipeline with a different example (e.g. `ml-basic`). That is because we used the `ml-intermediate` pipeline as the example, which already has parametrized products. Therefore, we need to add the `env.yaml` and parameterize the pipeline to run it successfully.

However, the `ml-basic` pipeline was not parametrized. Thus we need to parameterize it first. Please refer to [this documentation](https://docs.ploomber.io/en/latest/user-guide/parametrized.html) for more information on parametrized pipelines.
```

```{attention}
Make sure you delete your cluster, bucket, and image after running this example!

```sh
# delete cluster
gcloud container clusters delete my-cluster --zone us-east1-b

# delete bucket
gsutil rm -r gs://my-sample-ploomber-bucket

# delete image (you can get the image id from the google cloud console)
gcloud container images delete IMAGE-ID
```

### Optional: Mounting a shared disk

```{note}
If you use a shared disk instead of storing artifacts in S3 or Google Cloud
Storage, you must execute the pipeline with the `--skip-tests` flag. e.g.,
`soopervisor export training --skip-tests`, otherwise the command will
fail if your project does not have a remote storage client configured.
```

In the example, we configured the `pipeline.yaml` file to use Google Cloud
Storage to store artifacts, this serves two purposes: 1) Make artifacts
available to us upon execution, and 2) Make artifacts available to dowstream
tasks.

This happens because pods run in isolation, if task B depends on task A, it
will fetch A’s output from cloud storage before execution. We can save dowload
time (and cut costs) by mounting a shared volume so that B doesn’t have to
download A’s output. Ploomber automatically detects this change and only calls
the cloud storage API for uploading.

Here’s how to configure a shared disk:

```sh
# create disk. make sure the zone matches your cluster
gcloud compute disks create --size=10GB --zone=us-east1-b gce-nfs-disk

# configure the nfs server
curl -O https://raw.githubusercontent.com/ploomber/soopervisor/master/doc/assets/01-nfs-server.yaml
kubectl apply -f 01-nfs-server.yaml

# create service
curl -O https://raw.githubusercontent.com/ploomber/soopervisor/master/doc/assets/02-nfs-service.yaml
kubectl apply -f 02-nfs-service.yaml

# check service
kubectl get svc nfs-server

# create persistent volume claim
curl -O https://raw.githubusercontent.com/ploomber/soopervisor/master/doc/assets/03-nfs-pv-pvc.yaml
kubectl apply -f 03-nfs-pv-pvc.yaml
```

**Optionally**, you can check that the disk is properly configured by running this sample workflow:

```sh
# run sample workflow (uses nfs and creates an empty file on it)
curl -O https://raw.githubusercontent.com/ploomber/soopervisor/master/doc/assets/dag.yaml
argo submit -n argo --watch dag.yaml
```

Check the output:

```sh
# get nfs-server pod name
kubectl get pod

# replace with the name of the pod
kubectl exec --stdin --tty {nfs-server-pod-name} -- /bin/bash
```

Once inside the Pod, run:

```sh
ls /exports/
```

You should see files A, B, C, D. Generated by the previous workflow.

Let’s now run the Machine Learning workflow. Since we configured a shared disk,
artifacts from upstream tasks will be available to downstream ones (no need
to download them from Cloud Storage anymore); the Cloud Storage client is only used to upload
artifacts for us to review later.

To make the shared disk available to the pods that run each task, we have
to modify `soopervisor.yaml`:

```yaml
training:
  backend: argo-workflows
  repository: gcr.io/your-project/your-repository
  mounted_volumes:
    - name: nfs
      sub_path: my-shared-folder
      spec:
        persistentVolumeClaim:
          claimName: nfs
```

This exposes `/my-shared-folder` sub directory in our shared disk
in `/mnt/nfs/` on each pod. Now, we must configure the pipeline to store all
products in `/mnt/nfs/`. Create an `env.yaml` file in the root folder
(same folder that contains the `setup.py` file) with this content:

```yaml
sample: False
# this configures the pipeline to store all outputs in the shared disk
product_root: /mnt/nfs
```
