AWS Lambda
==========

.. note:: **Got questions?** Reach out to us on `Slack <http://community.ploomber.io/>`_.

`AWS Lambda <https://aws.amazon.com/lambda/>`_ is a serverless compute service.
It allows you to deploy functions in the cloud without worrying about servers
or scaling. It is a great (and cheap) option to deploy Machine Learning
models.

This tutorial shows you how to deploy a Machine Learning model to AWS Lambda.
Unlike other frameworks or tutorials, Soopervisor and Ploomber allow you to
deploy complete inference DAGs (as opposed to a model file) without changing
your training pipeline's code; handling packaging, containerization and
deployment.


If you encounter any issues with this
tutorial, `let us know <https://github.com/ploomber/soopervisor/issues/new?title=AWS%20Lambda%20tutorial%20problem>`_.

Pre-requisites
--------------

* `conda <https://docs.conda.io/en/latest/miniconda.html>`_
* `sam <https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html>`_
* `docker <https://docs.docker.com/get-docker/>`_
* `git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
* Install Ploomber with ``pip install ploomber``

Training vs. serving pipelines
------------------------------

When training an ML model, you may organize the pipeline in several tasks such
as "get data", "clean data", "compute feature 1", "compute feature 2" and
"train model".

To deploy the model, you have to provide both a model file and all the necessary
feature generation steps. Soopervisor and Ploomber allow you to create an
online inference pipeline from a training one without code changes.

In our case, your inference pipeline includes "compute feature 1" and
"compute feature 2"; and adds two new tasks: one to receive the input raw
data and another one to load a model and make a prediction using the feature
vector.

This tutorials will walk you through the development and deployment process.

Setting up project
------------------

We'll now fetch an example pipeline:

.. code-block:: sh

    git clone https://github.com/ploomber/projects
    cd projects/templates/ml-online/

Configure the development environment:

.. code-block:: sh

    ploomber install


Then, activate the environment:

.. code-block:: sh

    conda activate ml-online


Exploring the example code
--------------------------

Before diving into the code, let's plot our pipeline to have a better idea of
its structure:


.. code-block:: sh

    # required to generate plots
    conda install pygraphviz --channel conda-forge --yes

    # generate plot
    ploomber plot


Open the generated ``pipeline.png`` file. The left-most task in the pipeline
obtains data for training, then we have a couple tasks that geneate some
extra feature, a task that joins all features into a single data frame and
one that fits a model.

Those tasks are declared in the ``src/ml_online/pipeline.yaml`` file. Open the
file to review the content, you will see that there are two tasks in the
``tasks`` section (to get data and to fit the model), the remaining tasks
are coming from the ``src/ml_online/pipeline-features.yaml``; this separation
allows us to convert the feature engineering portion of the pipeline into
an inference pipeline without code changes.

Note that for this to work, all feature engineering tasks must be Python
functions with a configured ``serializer`` and ``unserializer``. The other
tasks can be of any type.

Training a model
----------------

Let's now train a model:

.. code-block:: sh

    ploomber build

Once the pipeline finishes, copy the trained model from
``products/model.pickle`` to the standard model location:
``src/ml_online/model.pickle``.

.. code-block:: sh

    # on linux/mac
    cp products/model.pickle src/ml_online/model.pickle


That's it. We're ready to export to AWS Lambda.


Generating files
----------------

Let's now create the necessary files to export to AWS Lambda:

.. code-block:: sh

    soopervisor add serve --backend aws-lambda


.. note::

    You don't have to install ``soopervisor`` manually; it should've been
    installed when running ``ploomber install``. If missing, install it with
    ``pip install soopervisor``.

You have to provide a few details before you can run the model in AWS Lambda.
First, edit the  ``serve/test_aws_lambda.py`` file. Such file contains a
unit test to ensure your model works as expected.

The test case is already configured, you only have to replace the line that
contaiins ``body = None`` for a sample input value. In our case, it looks
like this:

.. code-block:: python

    body = {
        'sepal length (cm)': 5.1,
        'sepal width (cm)': 3.5,
        'petal length (cm)': 1.4,
        'petal width (cm)': 0.2,
    }

.. important:: You should also remove the line that raises the ``NotImplementedError``.

Next, we have to tell Lambda, how to handle an incoming API request, this
happens in the ``serve/app.py`` file. The request body is received as a string
but our model receives a data frame as input. The sample code already
implements a "string to data frame" implementation, hence, you only have to
delete the line that raises the ``NotImplementedError``. When you use this
for your own model, write the applicable parsing logic.


To deploy to AWS Lambda, ``soopervisor`` packages your code and creates a
Docker image. We can build such Docker image (without actually deploying
to AWS Lambda) to test our API with the following command:

.. code-block:: sh

    soopervisor export serve --until-build


The command will take a few minutes since it has to create a Docker image,
subsequent runs will be much faster.

Once finished, you may start the API locally with:

.. code-block:: sh

    cd serve
    sam local start-api


Open a new terminal and call the API:

.. code-block:: sh

    curl http://127.0.0.1:3000/predict -X POST -d '{"sepal length (cm)": 5.1, "sepal width (cm)": 3.5, "petal length (cm)": 1.4, "petal width (cm)": 0.2}'

Try calling with other values to get a different prediction

.. note:: Due to the way the local API is built this will take a few seconds


**Congratulations! You just ran Ploomber on AWS Lambda!**

Deployment
**********

.. code-block:: sh

    soopervisor export serve

explain the --guided thing and add some link

you must be authenticated to use lambda, s3 and cloudformation

About ``template.yaml``
-----------------------

To deploy to Lamnda, AWS requires a ``template.yaml`` file to specify your
serverless application. A sample file that configures an API Gateway is
provided, but you may need to edit it for your application.
`Click here to learn more <https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html>`_.

