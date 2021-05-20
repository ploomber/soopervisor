Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor runs `Ploomber <github.com/ploomber/ploomber>`_ pipelines
for batch processing (large-scale training or batch serving) or online inference.

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

Soopervisor expects your Ploomber project to be in the standard project layout, which requires the following files:

1. ``environment.lock.yml``: `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_ with pinned dependencies
2. A ``pipeline.yaml`` file in the current working directory or in ``src/{package-name}/pipeline.yaml`` (if your project is a Python package)

.. note::

   If your project is a package (i.e., it has a ``src/`` directory, a 
   ``setup.py`` file is also required.

The easiest way to get started is to scaffold a new project with the following
commands:

.. code-block:: sh

   # install ploomber
   pip install ploomber

   # scaffold project
   ploomber scaffold


Then you can configure the development environment (which generates
the ``environment.lock.yml`` file) with:

.. code-block:: sh

   # move to your project's root folder
   cd {project-name}

   # configure dev environment
   ploomber install


If you prefer, you may use ``conda`` directly:

.. code-block::

   conda env export --no-build --file environment.lock.yml


Basic usage
===========

Soopervisor introduces the notion of *target platform*. Say, for example, that
you want to train multiple models in parallel, you may create a new target
environment to execute your pipeline in Kubernetes (using Argo Workflows):

.. code-block:: sh

   soopervisor add training --backend argo-workflows

After filling in some basic configuration settings, you can execute the
pipeline:

.. code-block:: sh

   soopervisor submit training

Ploomber will take care of packaging your code and submitting it for
execution. If using Argo Workflows, it will create a Docker image, upload it to
the configured registry, generate the Argo's YAML spec and submit the workflow.

Depending on the backend you select (Argo, Airflow, AWS Batch or AWS Lambda),
the configuration will change but the API remains the same:
``soopervisor add``, then ``soopervisor submit``.