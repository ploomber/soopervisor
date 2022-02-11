Kubernetes (Argo)
=================

.. note::

    This is a quick reference. For a full
    tutorial, :doc:`click here. <../tutorials/kubernetes>`


Step 1: Add target environment
------------------------------

.. code-block:: sh

    # add a target environment named 'argo'
    soopervisor add argo --backend argo-workflows

The command above will generate a pre-configured ``argo/Dockerfile``
and a new entry named ``argo`` in the ``soopervisor.yaml`` file. For
information on the configuration schema, :doc:`click here. <../api/kubernetes>`

At the very least, you'll have to modify ``repository`` to point it to the
container repository.

Step 2: Generate Argo Spec (``YAML``)
-------------------------------------

.. code-block:: sh

    # generate argo yaml spec
    soopervisor export argo --skip-tests  --ignore-git

The command will generate build the docker image, push it to the repository
and generate an Argo spec at ``argo/argo.yaml``.

Note that the command above will only export outdated tasks (the ones whose
source code has changed since the last execution), to force exporting all
tasks:

.. code-block:: sh

    # force exporting all tasks regardless of status
    soopervisor export argo --skip-tests  --ignore-git --mode force


.. important::

    For your pipeline to run successfully, tasks write their outputs in a
    common location. You can do this either by
    creating a shared disk or by adding a storage client.
    :doc:`Click here to learn more. <../user-guide/task-comm>`


To submit the workflow:

.. code-block:: sh

    # submit workflow
    argo submit -n argo argo/argo.yaml


For more information, refer
to `Argo's CLI documentation. <https://argoproj.github.io/argo-workflows/cli/>`_ 
