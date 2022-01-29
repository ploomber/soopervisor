Full workflow
=============

.. important:: This tutorial requires soopervisor ``0.6.1`` or higher

.. important::

    This tutorial requires ``soopervisor`` ``0.5.2`` or higher, and
    ``soorgeon`` ``0.0.2`` or higher.


This tutorial shows how to go from a monolithic Jupyter notebook to a
modular, production-ready pipeline deployed in workflow by using the tools
in our ecosystem:

1. `soorgeon <https://github.com/ploomber/soorgeon>`_
2. `ploomber <https://github.com/ploomber/ploomber>`_
3. `soopervisor <https://github.com/ploomber/soopervisor>`_

Pre-requisites
--------------

* `docker <https://docs.docker.com/get-docker/>`_

Building Docker image
---------------------

We provide a Docker image so you can quickly run this example:

.. code-block:: bash

    # get repository
    git clone https://github.com/ploomber/soopervisor
    cd soopervisor/tutorials/workflow

    # create a directory to store the pipeline output
    export SHARED_DIR=$HOME/ploomber-workflow
    mkdir -p $SHARED_DIR

    # build image
    docker build --tag ploomber-workflow .

    # start (takes ~1 minute to be ready)
    docker run -i -t \
        --privileged=true -v /var/run/docker.sock:/var/run/docker.sock \
        --volume $SHARED_DIR:/mnt/shared-folder \
        --env SHARED_DIR \
        --env PLOOMBER_STATS_ENABLED=false \
        -p 2746:2746 \
        ploomber-workflow


.. note::

    We need to run ``docker run`` in privileged mode since we'll be running
    ``docker`` commands inside the container.
    `More on that here <https://www.docker.com/blog/docker-can-now-run-within-docker/>`_

.. Upon initialization, JupyterLab will be running at https://127.0.0.1:8888


Refactor notebook
-----------------

First, we use ``soorgeon`` to refactor the notebook:

.. code-block:: bash

    soorgeon refactor nb.ipynb --product-prefix /mnt/shared-folder/output


We can generate a plot to visualize the dependencies:

.. code-block:: bash

    ploomber plot

If you open the generated ``pipeline.png``, you'll see that ``soorgeon``
inferred the dependencies among the sections in the notebook and built a
Ploomber pipeline automatically!

Now you can iterate this modular pipeline with Ploomber, but for now, let's
go to the next stage and deploy to Kubernetes.

Configure target platform
-------------------------

Soopervisor allows you to configure the target platform using a
``soopervisor.yaml`` file, let's add it and set the backend to
``argo-worflows``:

.. code-block:: bash

    soopervisor add training --backend argo-workflows


Usually, you'd manually edit ``soopervisor.yaml`` to configure your
environment; for this example, let's use one that we
`already configured <https://github.com/ploomber/soopervisor/blob/master/tutorials/workflow/soopervisor-workflow.yaml>`_,
which tells soopervisor to mount a local directory to every pod so we can review results later:

.. code-block:: bash

    cp /soopervisor-workflow.yaml soopervisor.yaml


Submit pipeline
---------------

We finished configuring; let's now submit the workflow:

.. code-block:: bash

    # build docker image and generate an argo's yaml spec
    soopervisor export training --skip-tests --ignore-git

    # import image to the k8s cluster
    k3d image import shared-folder:latest --cluster mycluster

    # submit workflow
    argo submit -n argo --watch training/argo.yaml


**Congratulations! You just went from a legacy notebook to production-ready pipeline! 🎉**

.. note::

    ``k3d image import`` is only required if creating the cluster with ``k3d``.


Once the execution finishes, take a look at the generated artifacts:

.. code-block:: sh

    ls /mnt/shared-folder


.. tip:: 

    You may also watch the progress from the UI.

    .. skip-next
    .. code-block:: sh

        # port forwarding to enable the UI
        kubectl -n argo port-forward svc/argo-server 2746:2746

    Then, open: https://127.0.0.1:2746

Clean up
--------

To delete the cluster:

.. code-block:: bash

    k3d cluster delete mycluster
