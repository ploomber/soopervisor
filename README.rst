Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor runs `Ploomber <github.com/ploomber/ploomber>`_ pipelines
for large-scale training, batch serving or online inference.

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

1. ``environment.lock.yml``: `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_
2. ``setup.py``: configuration file for packaging code

The easiest way to get started is to scaffold a new project with the following commands:

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


Once you have your project in the standard layour, you can start using
Soopervisor.

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
