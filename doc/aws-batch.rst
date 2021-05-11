AWS Batch
=========

`AWS Batch <https://aws.amazon.com/batch/>`_ is a managed service for batch
computing. This tutorial shows you how to submit a Ploomber pipeline to AWS
Batch.

Note that this tutorial involves several stages. If you encounter any issues,
`let us know <https://github.com/ploomber/soopervisor/issues/new?title=AWS%20Batch%20tutorial%20problem>`_.

Pre-requisites
--------------

Before continuing, make sure you have ``ploomber``, ``docker``, ``conda``
and ``aws``.

* `conda instructions <https://docs.conda.io/en/latest/miniconda.html>`_
* `docker instructions <https://docs.docker.com/get-docker/>`_
* `aws instructions <https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>`_
* `git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
* Install Ploomber with ``pip install ploomber``

``soopervisor`` takes your pipeline, packages it, creates a Docker image,
uploads it and submits it for execution; however, you still have to configure
the AWS Batch environment. Specifically, you must configure a compute
environment and a job queue. `Refer to this guide for instructions. <https://docs.aws.amazon.com/batch/latest/userguide/Batch_GetStarted.html>`_

**Note** Only EC2 compute environments are supported.

Once you've configured an EC2 compute environment and a job queue, continue to
the next step.

Setting up project
------------------

We'll now fetch an example pipeline:

.. code-block:: sh

    git clone https://github.com/ploomber/projects
    cd ml-online

Configure the development environment:

.. code-block:: sh

    ploomber install


Then, activate the environment:

.. code-block:: sh

    conda activate ml-online


Configure S3 client
-------------------

Now, we must configure a client to upload all generated artifacts to S3. To
obtain such credentials, you may use the AWS console, ensure you give read
and write S3 access. You may also create an S3 bucket or use one you already
have.

Save a ``credentials.json`` file in the root directory (the folder that contains
the ``setup.py`` file) with your authentication keys:

.. code-block:: json

    {
        "aws_access_key_id": "YOUR-ACCESS-KEY-ID",
        "aws_secret_access_key": "YOU-SECRET-ACCESS-KEY"
    }


Now, configure the pipeline to upload artifacts to S3. Modify the
``pipeline.yaml`` file at ``ml-online/src/ml_online/pipeline.yaml`` so
it looks like this:

.. code-block:: yaml

    meta:
      source_loader:
      module: ml_online

      import_tasks_from: pipeline-features.yaml

    # add this
    clients:
        File: ml_online.clients.get_s3

    # content continues...


Go to the ``src/ml_online/clients.py`` file and edit the ``get_s3`` function,
modify the ``bucket_name`` and ``parent`` parameters. The latter is the folder
inside the bucket where you want to save pipeline artifacts. Ignore the
second function; it's not relevant for this example.

To make sure your pipeline is properly configured, run:

.. code-block:: sh

    ploomber status

You should see a table with a summary. If you see an error, check the traceback
to see if it's an authentication problem or something else.


Submitting a pipeline to AWS Batch
----------------------------------

We are almost ready to submit. To execute tasks in AWS Batch, we must create
a Docker image with all our project's source code.

Create a new repository in `Amazon ECR <https://aws.amazon.com/ecr/>`_ before
continuing. Once you create it, authenticate with the following command
(replace ``your-repository-url/name`` with your repository's URL):

.. code-block:: sh

    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-repository-url/name


Let's now create the necessary files to export our Docker image:

**Note:** you don't have to install ``soopervisor`` manually; it should've
been installed when running ``ploomber install``. If missing, install it with
``pip install soopervisor``.

.. code-block:: sh

    soopervisor add training --backend aws-batch


Open the ``soopervisor.yaml`` file and fill in the missing values in
``repository``, ``job_queue`` and ``region_name``.

.. code-block:: yaml

    training:
      backend: aws-batch
      submit:
        repository: your-repository-url/name
        job_queue: your-job-queue
        region_name: your-region-name
        container_properties:
          memory: 16384
          vcpus: 8

Submit for execution:

.. code-block:: sh

    soopervisor submit training

The previous command will take a few minutes the first time since it has to
build the Docker image from scratch. Subsequent runs will be much faster.


**Note** if you successfully submit tasks, but they are stuck in the console in
``RUNNABLE`` status. It's likely that the requested resources (the
``container_properties`` section in ``soopervisor.yaml``) exceed the capacity
of the compute environment. Try lowering those resources and submit again. If
that doesn't work, `check this out <https://aws.amazon.com/premiumsupport/knowledge-center/batch-job-stuck-runnable-status/>`_.

**Congratulations! You just ran Ploomber on AWS Batch!**


Scaffolding projects
--------------------

For AWS Batch export to work, your project must be in standard form. This
involves packaging your code using a ``setup.py`` file, providing dependencies
via lock files, among other things. To ensure your projects are correctly
configured, we recommend using the ``ploomber scaffold command``.

.. code-block:: sh

    # create a base layout
    ploomber scaffold

    # add any extra dependencies to the setup.py file

    # setup the development environment
    ploomber install


