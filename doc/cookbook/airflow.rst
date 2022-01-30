Airflow
=======

Step 1: Add target environment
------------------------------

.. code-block:: sh

    # add a target environment named 'airflow' (using KubernetesPodOperator)
    soopervisor add airflow --backend airflow


.. note::

    Using the ``--preset`` option requires ``soopervisor>=0.7``

.. code-block:: sh

    # add a target environment named 'airflow-bash' (using BashOperator)
    soopervisor add airflow-bash --backend airflow --preset bash


.. code-block:: sh

    # add a target environment named 'airflow-k8s' (using KubernetesPodOperator)
    soopervisor add airflow-k8s --backend airflow --preset kubernetes


Step 1: Generate Airflow DAG
----------------------------


.. code-block:: sh

    # export target environment named 'airflow'
    soopervisor export airflow
