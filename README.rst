Soopervisor
===========


.. image:: https://github.com/ploomber/ci-for-ds/workflows/CI/badge.svg
   :target: https://github.com/ploomber/ci-for-ds/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor is a command line utility to execute
`Ploomber <github.com/ploomber/ploomber>`_-compatible projects.

Installation
------------

.. code-block:: sh

   pip install soopervisor

Usage
-----

For its simplest usage, ``soopervisor`` expects a project with a ``pipeline.yaml``
file, outputs saved in an ``output/`` directory and dependencies declared
in an `environment.yml <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually>`_ file

To execute a project:

.. code-block:: sh

   soopervisor build


Unlike ``ploomber build``, ``soopervisor build`` creates the environment first,
and then executes the pipeline (using ``ploomber build``). This ensures
dependency installation is part of the reproducibility process. But it
offers much more than just installing dependencies.

Configuration
-------------

An optional ``soopervisor.yaml`` file allows you to customize the build process.

Using Soopervisor for Continuous Integration
--------------------------------------------

[WIP]

Github action
-------------

[WIP]

Development
-----------

Once you cloned the repo:

.. code-block::

   pip install --editable ".[dev]"

To run tests:

.. code-block::

   pytest
