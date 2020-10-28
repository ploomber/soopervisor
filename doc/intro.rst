Introduction
============

Soopervisor introduces the concept of *Ploomber project*, which is a standard
way of running Ploomber pipelines.

When running a pipeline, Soopervisor expects the following file layout:

1. ``environment.yml``: `Conda environment specification <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually>`_
2. ``pipeline.yaml``: Ploomber pipeline specification

The parent folder to all these files is defined as the project's root folder.

If your project follows these two conventions, you'll be able to use Soopervisor
to run your project locally, continuous integration service or Apache Airflow.

How it works
============

Soopervisor first checks that the project has the right structure, if it finds
any issues, it reports them so you can fix them before you attempt to run the
pipeline.

If all checks pass, it generates a bash script to install the conda environment
and then run the pipeline.

How the script is used to actually execute the pipeline depends on your
configuration settings, the simplest case is to just run it locally, but you
can also tell Soopervisor to run the pipeline inside a Docker container or
to just generate the appropriate structure for Airflow to execute the pipeline.

Use cases
=========

There are currently three use cases for Soopervisor:

1. Running a pipeline locally
2. Running a pipeline in a continuous integration service
3. Running a pipeline using Apache Airflow