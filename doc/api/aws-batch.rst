AWS Batch
=========

Configuration schema for AWS Batch.

Basic example
-------------

.. code-block:: yaml
    :caption: soopervisor.yaml

    training:
        backend: aws-batch
        repository: your-repository-url/name
        job_queue: your-job-queue
        region_name: your-region-name
        container_properties:
            memory: 16384
            vcpus: 8


Custom resources
----------------

.. note::

    .. versionadded:: 0.8
        Custom resources via ``task_resources``

To set custom resources per task:

.. code-block:: yaml
    :caption: soopervisor.yaml

    training:
        backend: aws-batch
        repository: your-repository-url/name
        job_queue: your-job-queue
        region_name: your-region-name
        # this will the the default
        container_properties:
            memory: 16384
            vcpus: 8
            gpu: none
        task_resources:
            # replace task_name with the actual task name
            # in your pipeline
            task_name:
                memory: 16384
                vcpus: 4
                gpu: 1
            # you can also use wildcards, to match all tasks with the
            # fit- prefix
           fit-*:
                memory: 16384
                vcpus: 4
                gpu: 1


Schema
-------

.. autoclass:: soopervisor.abc.AbstractConfig


.. autoclass:: soopervisor.aws.config.AWSBatchConfig


.. autoclass:: soopervisor.aws.config.TaskResource