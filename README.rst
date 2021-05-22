Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge


Soopervisor runs `Ploomber <github.com/ploomber/ploomber>`_ pipelines
for batch processing (large-scale training or batch serving) or online
inference.

.. code-block:: sh

   pip install soopervisor


Check out the `documentation <https://soopervisor.readthedocs.io/>`_ to learn more.

Supported platforms
===================

* Batch serving and large-scale training:

  * Kubernetes / Argo Workflows
  * AWS Batch

* Online inference:

  * AWS Lambda

Usage
=====

Say that you want to train multiple models in a Kubernetes
cluster, you may create a new target environment to execute your pipeline
using Argo Workflows:

.. code-block:: sh

   soopervisor add training --backend argo-workflows

After filling in some basic configuration settings, export the pipeline with:

.. code-block:: sh

   soopervisor export training


Depending on the selected backend (Argo, Airflow, AWS Batch or AWS Lambda),
configuration details will change but the API remains the same:
``soopervisor add``, then ``soopervisor export``.