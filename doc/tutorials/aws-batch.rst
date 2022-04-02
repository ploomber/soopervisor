AWS Batch
=========

.. important:: This tutorial requires soopervisor ``0.6.1`` or higher

.. note:: **Got questions?** Reach out to us on `Slack <https://ploomber.io/community/>`_.

`AWS Batch <https://aws.amazon.com/batch/>`_ is a managed service for batch
computing. This tutorial shows you how to submit a Ploomber pipeline to AWS
Batch.

If you encounter any issues with this
tutorial, `let us know <https://github.com/ploomber/soopervisor/issues/new?title=AWS%20Batch%20tutorial%20problem>`_.

`Click here to see a recorded demo <https://youtu.be/XCgX1AszVF4>`_.

Pre-requisites
--------------

* `conda <https://docs.conda.io/en/latest/miniconda.html>`_
* `docker <https://docs.docker.com/get-docker/>`_
* `aws cli <https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>`_
* `git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_

``soopervisor`` takes your pipeline, packages it, creates a Docker image,
uploads it, and submits it for execution; however, you still have to configure
the AWS Batch environment. Specifically, you must configure a computing
environment and a job queue. `Refer to this guide for instructions. <https://docs.aws.amazon.com/batch/latest/userguide/Batch_GetStarted.html>`_

.. note:: Only EC2 compute environments are supported.

Once you've configured an EC2 compute environment and a job queue, continue to
the next step.

Setting up project
------------------

First, let's install ``ploomber``:

.. code-block:: sh

    pip install ploomber

Fetch an example pipeline:

.. code-block:: sh

    # get example
    ploomber examples -n templates/ml-online -o ml-online
    cd ml-online

Configure the development environment:

.. code-block:: sh

    ploomber install


Then, activate the environment:

.. code-block:: sh

    conda activate ml-online


Configure S3 client
-------------------

We must configure a client to upload all generated artifacts to S3. To
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
modifying the ``bucket_name`` and ``parent`` parameters. The latter is the folder
inside the bucket to save pipeline artifacts. Ignore the
second function; it's not relevant for this example.

To make sure your pipeline works, run:

.. code-block:: sh

    ploomber status

You should see a table with a summary. If you see an error, check the traceback
to see if it's an authentication problem or something else.


Submitting a pipeline to AWS Batch
----------------------------------

We are almost ready to submit. To execute tasks in AWS Batch, we must create
a Docker image with all our project's source code.

Create a new repository in `Amazon ECR <https://aws.amazon.com/ecr/>`_ before
continuing. Once you create it, authenticate with:

.. code-block:: sh

    aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-repository-url/name


.. note::

    Replace ``your-repository-url/name`` with your repository's URL and
    ``your-region`` with the corresponding ECR region


Let's now create the necessary files to export our Docker image:

.. code-block:: sh

    # get soopervisor
    pip install soopervisor

    # register new environment
    soopervisor add training --backend aws-batch


Open the ``soopervisor.yaml`` file and fill in the missing values in
``repository``, ``job_queue`` and ``region_name``.

.. code-block:: yaml

    training:
      backend: aws-batch
      repository: your-repository-url/name
      job_queue: your-job-queue
      region_name: your-region-name
      container_properties:
        memory: 16384
        vcpus: 8

Submit for execution:

.. code-block:: sh

    soopervisor export training --skip-tests --ignore-git

The previous command will take a few minutes since it has to
build the Docker image from scratch. After that, subsequent runs will be much faster.


.. note:: 

    if you successfully submitted tasks, but they are stuck in the console in
    ``RUNNABLE`` status. It's likely that the requested resources (the
    ``container_properties`` section in ``soopervisor.yaml``) exceeded the capacity
    of the computing environment. Try lowering resources and submit again. If
    that doesn't work, `check this out <https://aws.amazon.com/premiumsupport/knowledge-center/batch-job-stuck-runnable-status/>`_.

.. tip::

    The number of concurrent jobs is limited by the resources in the Compute
    Environment. Increase them to run more tasks in parallel.

**Congratulations! You just ran Ploomber on AWS Batch!**

