.. _k8s-local:

Local example
-------------

.. important:: This tutorial requires soopervisor ``0.5.2`` or higher

This tutorial runs a pipeline in a local Kubernetes cluster using ``k3d``.

Pre-requisites
**************

* `docker <https://docs.docker.com/get-docker/>`_

Building Docker image
*********************

We provide a Docker image so you can quickly run this example:

.. code-block:: bash

    # get repository
    git clone https://github.com/ploomber/soopervisor
    cd soopervisor/tutorials/kubernetes

    # create a directory to store the pipeline output
    export SHARED_DIR=$HOME/ploomber-k8s
    mkdir -p $SHARED_DIR

    # build image
    docker build --tag ploomber-k8s .

    # start
    docker run \
        --privileged=true -v /var/run/docker.sock:/var/run/docker.sock \
        --volume $SHARED_DIR:/mnt/shared-folder \
        --env SHARED_DIR \
        -p 2746:2746 \
        -i -t ploomber-k8s /bin/bash

Create Kubernetes cluster
*************************

The Docker image comes with ``k3d`` pre-installed; let's create a cluster:

.. code-block:: bash

    # create cluster
    k3d cluster create mycluster --volume $SHARED_DIR:/host --port 2746:2746

    # check cluster
    kubectl get nodes


Install Argo
************

We now install argo; note that we are using a custom installation file
(``argo-pns.yaml``) to ensure this works with ``k3d``.

.. code-block:: bash

    # install argo
    kubectl create ns argo
    kubectl apply -n argo -f argo-pns.yaml

    # check argo pods (once they're all running, argo is ready)
    kubectl get pods -n argo


.. tip::
    Optionally, submit sample Argo workflow to ensure everything is working:

    .. code-block:: bash

        argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml


Get sample Ploomber pipeline
****************************

.. code-block:: bash

    # get example
    ploomber examples -n templates/ml-intermediate -o ml-intermediate
    cd ml-intermediate

    # configure development environment
    cp environment.yml environment.lock.yml
    pip install ploomber soopervisor
    pip install -r requirements.txt


Configure target platform
*************************

Soopervisor allows you to configure the target platform using a
``soopervisor.yaml`` file, let's add it and set the backend to
``argo-worflows``:

.. code-block:: bash

    soopervisor add training --backend argo-workflows


Usually, you'd manually edit ``soopervisor.yaml`` to configure your
environment; for this example, let's use one that we
`already configured <https://github.com/ploomber/soopervisor/blob/master/tutorials/kubernetes/soopervisor-k8s.yaml>`_,
which tells soopervisor to mount a local directory to every pod so we can review results later:

.. code-block:: bash

    cp ../soopervisor-k8s.yaml soopervisor.yaml


We must configure the project to store all outputs in the shared folder, so we
copy the `pre-configured file <https://github.com/ploomber/soopervisor/blob/master/tutorials/kubernetes/env-k8s.yaml>`_:

.. code-block:: bash

    cp ../env-k8s.yaml env.yaml


Submit pipeline
***************

We finished configuring; let's now submit the workflow:

.. code-block:: bash

    # build docker image (takes a few minutes the first time) and generate an argo's yaml spec
    soopervisor export training --skip-tests

    # import image to the k8s cluster
    k3d image import ml-intermediate:latest --cluster mycluster

    # submit workflow
    argo submit -n argo --watch training/argo.yaml


**Congratulations! You just ran Ploomber on Kubernetes! 🎉**

.. note::

    ``k3d image import`` is only required if creating the cluster with ``k3d``.


Once the execution finishes, take a look at the generated artifacts:

.. code-block:: sh

    ls /mnt/shared-folder


.. tip:: 

    You may also watch the progress from the UI.

    .. code-block:: sh

        # port forwarding to enable the UI
        kubectl -n argo port-forward svc/argo-server 2746:2746

    Then, open: https://127.0.0.1:2746


Incremental builds
******************

Try exporting the pipeline again:

.. code-block:: bash

    soopervisor export training --skip-tests


You'll see a message like this: ``Loaded DAG in 'incremental' mode has no tasks to submit``.
Soopervisor checks the status of your pipeline and only schedules tasks that have changed
since the last run; since all your tasks are the same, there is nothing to run!

Let's now modify one of the tasks and submit again:

.. code-block:: bash

    # modify the fit.py task, add a print statement
    echo -e "\nprint('Hello from Kubernetes')" >> fit.py

    # re-build docker image and submit
    soopervisor export training --skip-tests
    k3d image import ml-intermediate:latest --cluster mycluster
    argo submit -n argo --watch training/argo.yaml

You'll see that this time, only the ``fit`` task ran, because that's the only
tasks whose source code change, we call this incremental builds, and they're a
great feature for quickly running experiments in your pipeline such as changing
model hyperparameters or adding new pre-processing methods; it saves a lot of
time since you don't have to execute the entire pipeline every time.


Clean up
********

To delete the cluster:

.. code-block:: bash

    k3d cluster delete mycluster

