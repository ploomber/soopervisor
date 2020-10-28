Soopervisor
===========


.. image:: https://github.com/ploomber/ci-for-ds/workflows/CI/badge.svg
   :target: https://github.com/ploomber/ci-for-ds/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor is a command line utility to execute and export
`Ploomber <github.com/ploomber/ploomber>`_-compatible projects.

Main features
-------------

* Export a Ploomber project to Airflow
* Execute pipeline locally (in a subprocess or docker container) and keep execution history
* Execute a pipeline in a Continuous Integration server

Installation
------------

.. code-block:: sh

   pip install soopervisor


Development
-----------

Once you cloned the repo:

.. code-block::

   pip install --editable ".[dev]"

To run tests:

.. code-block::

   pytest
