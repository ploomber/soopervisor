Command line interface
======================

Soopervisor has two commands, ``add`` and ``export``.

``soopervisor add``
-------------------

Adds a new target environment:


.. code-block:: sh

    soopervisor add {name} --backend {backend}

Where ``{backend}`` is one of ``aws-batch``, ``aws-lambda``,
``argo-workflows``, or ``airflow``.


``soopervisor export``
----------------------

Exports an existing target environment:


.. code-block:: sh

    soopervisor export {name}

Where ``{name}`` is previously added target environment.

``--mode {mode}``
*****************

Allows you to export the pipeline in several ways:

* ``incremental`` (default) only export tasks whose source has changed 
* ``regular`` all tasks are exported, status (execute/skip) determined at runtime
* ``force`` all tasks are exported and executed regardless of status

Example:

.. code-block:: sh

    soopervisor export {name} --mode force

``--skip-tests``
****************

Soopervisor tests the pipeline before submitting, use this flag to skip testing.


Example:

.. code-block:: sh

    soopervisor export {name} --skip-tests