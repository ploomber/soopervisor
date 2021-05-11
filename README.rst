Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor lets you run `Ploomber <github.com/ploomber/ploomber>`_ pipelines for large-scale workloads or online inference.

Supported platforms
===================

* Large scale workloads:

  * Kubernetes / Argo Workflows
  * AWS Batch

* Online inference:

  * AWS Lambda


Standard layout
===============

Soopervisor expects your Ploomber project to be in the standard project layout, which requires the following files:

1. ``environment.yml``: `Conda environment specification <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_
2. ``setup.py``: File for packaging code

You can scaffold a new project with the following command:

.. code-block:: sh

   ploomber scaffold


Basic usage
===========

Soopervisor introduces the notion of *target platform* which defines the
configuration and format to export your projects. Say, for example, that you want
to train multiple models in parallel, you may create a new target platform like this:

.. code-block:: sh

   soopervisor add training --backend argo-workflows

After filling in some basic configuration settings (which depend on the chosen platform):

.. code-block:: sh

   soopervisor submit training

Ploomber will take care of packaging and submitting your pipeline for execution. In this case,
it will create a Docker image, upload the image to a registry, generate the Argo's YAML spec and
submit the workload.

Installation
============

.. code-block:: sh

   pip install soopervisor
