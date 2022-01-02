Airflow
=======

.. note:: **Got questions?** Reach out to us on `Slack <https://ploomber.io/community/>`_.

This tutorial shows you how to export a Ploomber pipeline to Airflow.

If you encounter any issues with this
tutorial, `let us know <https://github.com/ploomber/soopervisor/issues/new?title=Airflow%20tutorial%20problem>`_.

Pre-requisites
--------------

* `docker <https://docs.docker.com/get-docker/>`_


Building Docker image
---------------------

We provide a Docker image so you can quickly run this example:

.. code-block:: bash

    # get repository
    git clone https://github.com/ploomber/soopervisor
    cd soopervisor/tutorials/airflow

    # create a directory to store the pipeline output
    export SHARED_DIR=$HOME/ploomber-airflow
    mkdir -p $SHARED_DIR

    # build image
    docker build --tag ploomber-airflow .

    # start
    docker run -p 8080:8080 --privileged=true \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --volume $SHARED_DIR:/mnt/shared-folder \
        --env SHARED_DIR \
        -i -t ploomber-airflow


Create Kubernetes cluster
-------------------------

By default, the Airflow integration exports each task in your pipeline as a
Airflow task using the `KubernetesPodOperator <https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html>`_,
so we need to create a Kubernetes cluster to run the example:

The Docker image comes with ``k3d`` pre-installed; let's create a cluster:

.. code-block:: bash

    # create cluster
    k3d cluster create mycluster --volume $SHARED_DIR:/host

    # check cluster
    kubectl get nodes


Get sample Ploomber pipeline
-----------------------------

.. code-block:: bash

    # get example
    ploomber examples -n templates/ml-intermediate -o ml-intermediate
    cd ml-intermediate

    cp environment.yml environment.lock.yml
    # configure development environment
    pip install ploomber soopervisor
    pip install -r requirements.txt


Configure target platform
-------------------------

.. code-block:: bash

    # add a new target platform
    soopervisor add training --backend airflow

Usually, you'd manually edit ``soopervisor.yaml`` to configure your
environment; for this example, let's use one that we
`already configured <https://github.com/ploomber/soopervisor/blob/master/tutorials/airflow/soopervisor-airflow.yaml>`_,
which tells soopervisor to mount a local directory to every pod so we can review results later:

.. code-block:: bash

    cp ../soopervisor-airflow.yaml soopervisor.yaml


We must configure the project to store all outputs in the shared folder, so we
copy the `pre-configured file <https://github.com/ploomber/soopervisor/blob/master/tutorials/airflow/env-airflow.yaml>`_:

.. code-block:: bash

    cp ../env-airflow.yaml env.yaml


Submit pipeline
---------------
    
.. code-block:: bash

    soopervisor export training --skip-tests

    # import image to the cluster
    k3d image import ml-intermediate:latest --cluster mycluster


Once the export process finishes, you'll see a new ``training/`` folder with
two files: ``ml-intermediate.py`` which is the Airflow DAG and
``ml-intermediate.json`` which contains the DAG structure.

Customizing Airflow DAG
-----------------------

.. code-block:: bash

    cp ../ml-intermediate.py training/ml-intermediate.py


Submitting pipeline
-------------------

To deploy, move those files to your ``AIRFLOW_HOME``.

For example, ``AIRFLOW_HOME`` is ``~/airflow``:

.. code-block:: bash

    mkdir -p /root/airflow/dags
    cp training/ml-intermediate.py ~/airflow/dags
    cp training/ml-intermediate.json ~/airflow/dags

    ls /root/airflow/dags


If everything is working, you should see the ``ml-intermediate`` DAG:

.. code-block:: sh

    airflow dags list

Let's trigger a run:

.. airflow is not picking up the new dag, even though it shows after running "airfow dags list", I had to restart it

.. code-block:: bash

    pkill -f airflow
    cd / && ./start_airflow.sh

.. code-block:: sh

    airflow dags unpause ml-intermediate
    airflow dags trigger ml-intermediate


**Congratulations! You just ran Ploomber on Airflow! 🎉**

Monitoring execution status
---------------------------

You may track execution progress from Airflow's UI by opening
http://localhost:8080 (Username: ``ploomber``, Password: ``ploomber``)


Alternatively, with the following command:

.. code-block:: sh

    airflow dags state ml-intermediate {TIMESTAMP}


The TIMESTAMP shows after running ``airflow dags trigger ml-intermediate``,
for example, once you execute the ``airflow dags trigger`` command, you'll see
something like this in the console:

    Created <DagRun ml-intermediate @ 2022-01-02T18:05:19+00:00: manual__2022-01-02T18:05:19+00:00, externally triggered: True>


Then, you can get the execution status with:

.. code-block:: sh

    airflow dags state ml-intermediate 2022-01-02T18:05:19+00:00


Incremental builds
------------------

.. TODO


Clean up
--------

To delete the cluster:

.. code-block:: bash

    k3d cluster delete mycluste


Airflow DAG customization
-------------------------

The generated Airflow pipeline consists of ``DockerOperator`` tasks. You may
edit the generated file (in our case ``serve/ml-intermediate.py`` and customize
it to suit your needs. Since the Docker image is already configured, you can
easily switch to ``KubernetesPodOperator`` tasks.

Using the DockerOperator
------------------------

.. attention::

    Due to a
    `bug in the DockerOperator <https://github.com/apache/airflow/issues/13487>`_,
    we must set ``enable_xcom_pickling = True`` in ``airflow.cfg`` file. By
    default, this file is located at ``~/airflow/airflow.cfg``.
