Soopervisor
===========

Soopervisor runs `Ploomber <github.com/ploomber/ploomber>`_ pipelines
for batch processing (large-scale training or batch serving) or online
inference.

.. code-block:: sh

   pip install soopervisor

Supported platforms
===================

* Batch serving and large-scale training:

  * Kubernetes / Argo Workflows
  * AWS Batch

* Online inference:

  * AWS Lambda


Standard layout
===============

Soopervisor expects your Ploomber project to be in the standard project
layout, which requires the following:

Dependencies file
*****************

* ``requirements.lock.txt``: ``pip`` dependencies file

.. tip:: You can generate it with ``pip freeze > requirements.lock.txt``

OR

* ``environment.lock.yml``: `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_ with pinned dependencies

.. tip:: You can generate it with ``conda env export --no-build --file environment.lock.yml``

Pipeline declaration
********************

A ``pipeline.yaml`` file in the current working directory
(or in ``src/{package-name}/pipeline.yaml`` if your project is a Python
package).

.. note::

   If your project is a package (i.e., it has a ``src/`` directory, a 
   ``setup.py`` file is also required.

Scaffolding standard layout
***************************

The fastest way to get started is to scaffold a new project:

.. code-block:: sh

   # install ploomber
   pip install ploomber

   # scaffold project
   ploomber scaffold

   # or to use conda (instead of pip)
   ploomber scaffold --conda

   # or to use the package structure
   ploomber scaffold --package

   # or to use conda and the package structure
   ploomber scaffold --conda --package


Then, configure the development environment:

.. code-block:: sh

   # move to your project's root folder
   cd {project-name}

   # configure dev environment
   ploomber install


.. note::

   ``ploomber install`` automatically generates the
   ``environment.lock.yml`` or ``requirements.lock.txt`` file. If you prefer so,
   you may skip ``ploomber install`` and generate the lock files yourself.

Usage
=====

Say that you want to train multiple models in a Kubernetes
cluster, you may create a new target environment to execute your pipeline
using Argo Workflows:

.. code-block:: sh

   soopervisor add training --backend argo-workflows

After filling in some basic configuration settings, export the pipeline with:

.. code-block:: sh

   soopervisor export training

Soopervisor will take care of packaging your code and submitting it for
execution. If using Argo Workflows, it will create a Docker image, upload it to
the configured registry, generate an Argo's YAML spec and submit the workflow.

Depending on the selected backend (Argo, Airflow, AWS Batch or AWS Lambda),
configuration details will change but the API remains the same:
``soopervisor add``, then ``soopervisor export``.


.. toctree::
   :caption: Batch processing
   :hidden:

   tutorials/kubernetes
   tutorials/aws-batch
   tutorials/airflow


.. toctree::
   :caption: Online inference
   :hidden:

   tutorials/aws-batch


.. toctree::
   :caption: External links
   :hidden:

   Github <https://github.com/ploomber/soopervisor>
   Ploomber <https://github.com/ploomber/ploomber>
   Blog <https://ploomber.io>

