Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor introduces the concept of a *Ploomber project*, which is a standard
way of running `Ploomber <github.com/ploomber/ploomber>`_ pipelines.


Use cases
=========

1. Running a pipeline locally
2. Running a pipeline in a continuous integration service
3. Scheduling a pipeline using cron (or Github Actions)
4. Running in Kubernetes via Argo workflows
5. Running in Apache Airflow


How it works
============

When running a pipeline, Soopervisor expects the following file layout:

1. ``environment.yml``: `Conda environment specification <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_
2. ``pipeline.yaml``: Ploomber pipeline specification

The parent folder to all these files is defined as the project's root folder.
The name of such folder is designed as the project's name.

For example if your ``pipeline.yaml`` is located at
``/path/to/projects/some-project/pipeline.yaml``, your project's root folder
is ``/path/to/projects/some-project`` and your project's name is
``some-project``.

If your project follows these two conventions, you'll be able to use Soopervisor
to run your project locally, continuous integration service or Apache Airflow.


Project validation
==================

Before building/exporting your project, Soopervisor first checks that the
project has the right structure, if it finds any issues, it reports them so you
can fix them before you attempt to run the pipeline.

If all checks pass, it generates a bash script to install the conda environment
and then run the pipeline.

How the script is used to actually execute the pipeline depends on your
configuration settings, the simplest case is to just run it locally, but you
can also tell Soopervisor to run the pipeline inside a Docker container or
to just export your project to run in Kubernetes (using Argo) or Airflow.


Installation
============

.. code-block:: sh

   pip install soopervisor
