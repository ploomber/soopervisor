Command line interface
======================

Soopervisor has two commands, ``add`` and ``export``.

``soopervisor add``
-------------------

**Adds a new target environment:**

.. code-block:: sh

    soopervisor add {name} --backend {backend}


* ``{name}`` is any identifier you want to identify this configuration
* ``{backend}`` is one of ``aws-batch``, ``aws-lambda``, ``argo-workflows``, ``airflow``, or ``slurm``

The command adds a new section in a ``soopervisor.yaml`` file (creates one if
needed) with the ``{name}``, and adds a few necessary files in a ``{name}``
directory.

**Example:**

.. code-block:: sh

    soopervisor add train-cluster --backend argo-workflows


``soopervisor export``
----------------------

**Exports a target environment:**


.. code-block:: sh

    soopervisor export {name}

Where ``{name}`` is the name of a target environment.


``soopervisor export`` has a few options.

Execution mode: ``--mode {mode}``/ ``-m``
*****************************************

* ``incremental`` (default) only export tasks whose source has changed.
* ``regular`` all tasks are exported, status (execute/skip) determined at runtime.
* ``force`` all tasks are exported and executed regardless of status.


Example:

.. code-block:: sh

    soopervisor export train-cluster --mode force


``--ignore-git`` / ``-i``
*************************

.. note:: ``--ignore-git`` has no effect when using SLURM

If you are using ``soopervisor`` inside a git repository, ``soopervisor`` will
only copy the files tracked by your repository into the Docker image. For
example, if you have a ``secrets.json`` file, but your ``.gitignore`` file
has a ``secrets.json`` entry, ``soopervisor`` wil not copy it to the Docker
image. If you pass ``--ignore-git``, **the status of your git repository is
ignored and all files are copied.**

Example:

.. code-block:: sh

    soopervisor export train-cluster --ignore-git


``--skip-tests`` / ``-s``
*************************

.. note:: ``--skip-tests`` has no effect when using SLURM

Soopervisor tests the pipeline before submitting, for example, it checks that
a ``File.client`` is configured, use this flag to **skip docker image tests**:


Example:

.. code-block:: sh

    soopervisor export train-cluster --skip-tests


``--skip-docker``
*************************

.. note:: ``--skip-docker`` has no effect when using SLURM

    .. versionadded:: 0.8.1

         Added `--skip-docker` option to `soopervisor export`      

Soopervisor allows you to build a docker image, use this flag to **skip docker image build step**:


Example:

.. code-block:: sh

    soopervisor export train-cluster --skip-docker