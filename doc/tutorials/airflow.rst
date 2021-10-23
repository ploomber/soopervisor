Airflow
=======

.. note:: **Got questions?** Reach out to us on `Slack <http://community.ploomber.io/>`_.

This tutorial shows you how to export a Ploomber pipeline to Airflow.

If you encounter any issues with this
tutorial, `let us know <https://github.com/ploomber/soopervisor/issues/new?title=Airflow%20tutorial%20problem>`_.


.. note::

    This tutorial uses cloud storage (S3 or Google Cloud Storage). If you're
    looking for an example that doesn't require any cloud services. Check out
    the minikube example: :ref:`minikube-example`


Pre-requisites
**************
* `airflow <https://airflow.apache.org/docs/apache-airflow/stable/start/index.html>`_
* ``conda`` `See instruction shere <https://docs.conda.io/en/latest/miniconda.html>`_
* `docker <https://docs.docker.com/get-docker/>`_
* `git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
* Install Ploomber with ``pip install ploomber``

.. note::

    When installating Airflow, you must install Docker dependencies,
    ``pip install "apache-airflow[docker]"`` should work


Instructions
------------


Let's now pull some sample code:

.. code-block:: sh

    # get the sample projects
    git clone https://github.com/ploomber/projects

    cd projects/ml-intermediate/


Since each task executes in a different Docker container, we have to configure
cloud storage for tasks to share data. Modify the ``environment.yml`` file and
add the appropriate dependency:

.. code-block:: yaml

    # content...
    - pip:
      # dependencies...

      # add your dependency here
      - boto3 # if you want to use S3
      - google-cloud-storage # if you want to use Google Cloud Storage

We also need to configure the pipeline to use cloud storage, open the
``pipeline.yaml`` file and add the following next to the ``meta`` section.\

.. tab:: S3

    .. code-block:: yaml

        meta:
            # some content...

        clients:
            File: clients.get_s3

.. tab:: GCloud

    .. code-block:: yaml

        meta:
            # some content...

        clients:
            File: clients.get_gcloud

Now, edit the ``clients.py`` file, you only need to change the ``bucket_name``
parameter for the corresponding function. For example if using a bucket with
name ``bucket-name`` and S3, ``clients.py`` should look like this:


.. tab:: S3

    .. code-block:: python

        from ploomber.clients import S3Client

        def get_s3():
            return S3Client(bucket_name='bucket-name',
                            parent='ml-intermediate',
                            json_credentials_path='credentials.json')

.. tab:: GCloud

    .. code-block:: python

        from ploomber.clients import GCloudStorageClient

        def get_gcloud():
            return GCloudStorageClient(bucket_name='bucket-name',
                                       parent='ml-online',
                                       json_credentials_path='credentials.json')


To authenticate to the cloud storage service, add a ``credentials.json``
file in the project root (same folder that has the ``environment.yml`` file.


.. tab:: S3

    .. code-block:: json

        {
            "aws_access_key_id": "YOUR-ACCESS-KEY-ID",
            "aws_secret_access_key": "YOU-SECRET-ACCESS-KEY"
        }


.. tab:: GCloud

    .. code-block:: json
    
        {
            "type": "service_account",
            "project_id": "project-id",
            "private_key_id": "private-key-id",
            "private_key": "private-key",
            "client_email": "client-email",
            "client_id": "client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account.iam.gserviceaccount.com"
        }
  
  

Let's now create the virtual environment:

.. code-block:: sh

    # configure environment
    conda env create --file environment.yml

    # activate environment
    conda activate ml-intermediate

    # generate lock file
    conda env export --no-build --file environment.lock.yml


Let's now verify that everything is configured correctly:

.. code-block:: sh

    ploomber status

We now export the pipeline to Airflow:

.. code-block:: sh

    soopervisor add train --backend airflow


.. note::

    You don't have to install ``soopervisor`` manually; it should've been
    installed when running ``ploomber install``. If missing, install it with
    ``pip install soopervisor``.

``soopervisor add`` creates a few new files. Let's configure
``soopervisor.yaml`` which controls some settings:


.. code-block:: yaml

    train:
      backend: airflow
      # we will be using docker locally, we set this to null
      repository: null
      # make sure our credentials are included when building the image
      include: [credentials.json]


Build the Docker image (takes a few mins the first time):
    
.. code-block:: sh

    soopervisor export train


Once the export process finishes, you'll see a new ``train/`` folder with
two files: ``ml-intermediate.py`` which is the Airflow DAG and
``ml-intermediate.json`` which contains information for instantiating the DAG.
To deploy, move those files to your ``AIRFLOW_HOME``.

For example, if ``AIRFLOW_HOME`` is set to ``~/airflow``
(this is the default value when installing Airflow):

.. code-block:: sh

    mkdir -p ~/airflow/dags
    cp train/ml-intermediate.py ~/airflow/dags
    cp train/ml-intermediate.json ~/airflow/dags


.. attention::

    Due to a
    `bug in the DockerOperator <https://github.com/apache/airflow/issues/13487>`_,
    we must set ``enable_xcom_pickling = True`` in ``airflow.cfg`` file. By
    default, this file is located at ``~/airflow/airflow.cfg``.

We're ready to run the pipeline! Start the Airflow scheduler:

.. code-block:: sh

    airflow scheduler

In a new terminal, start the web server:

.. code-block:: sh

    airflow webserver --port 8080

.. note::

    To log in to the web server, you must the credentials configured as part
    of the setup process when running the ``airflow users create`` command.


If everything is working, you should see the ``ml-intermediate`` DAG:


.. code-block:: sh

    airflow dags list


Let's trigger a run:


.. code-block:: sh

    airflow dags unpause ml-intermediate
    airflow dags trigger ml-intermediate

You can check the status in the UI.

Alternatively, with the following command:

.. code-block:: sh

    airflow dags state ml-intermediate "TIMESTAMP"


.. note:: The TIMESTAMP is printed after running ``airflow dags trigger ml-intermediate``
    


Airflow DAG customization
-------------------------

The generated Airflow pipeline consists of ``DockerOperator`` tasks. You may
edit the generated file (in our case ``serve/ml-intermediate.py`` and customize
it to suit your needs. Since the Docker image is already configured, you can
easily switch to ``KubernetesPodOperator`` tasks.
