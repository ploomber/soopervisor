Soopervisor
===========

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge

.. image:: https://github.com/ploomber/soopervisor/workflows/CI%20macOS/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI%20macOS/badge.svg
   :alt: CI macOS badge

.. image:: https://github.com/ploomber/soopervisor/workflows/CI%20Windows/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI%20Windows/badge.svg
   :alt: CI Windows badge


Soopervisor runs `Ploomber <https://github.com/ploomber/ploomber>`_ pipelines
for batch processing (large-scale training or batch serving) or online
inference.

.. code-block:: sh

   pip install soopervisor


Check out the `documentation <https://soopervisor.readthedocs.io/>`_ to learn more.

*Compatible with Python 3.7 and higher.*

Supported platforms
===================

* Batch serving and large-scale training:

  * `Airflow <https://soopervisor.readthedocs.io/en/latest/tutorials/airflow.html>`_
  * `Argo/Kubernetes <https://soopervisor.readthedocs.io/en/latest/tutorials/kubernetes.html>`_
  * `AWS Batch <https://soopervisor.readthedocs.io/en/latest/tutorials/aws-batch.html>`_
  * `Kubeflow <https://soopervisor.readthedocs.io/en/latest/tutorials/kubeflow.html>`_
  * `SLURM <https://soopervisor.readthedocs.io/en/latest/tutorials/slurm.html>`_

* Online inference:

  * `AWS Lambda <https://soopervisor.readthedocs.io/en/latest/tutorials/aws-lambda.html>`_


From notebook to a production pipeline
======================================

We also have `an example <https://soopervisor.readthedocs.io/en/latest/tutorials/workflow.html>`_ that shows how to use our ecosystem of tools to
go **from a monolithic notebook to a pipeline deployed in Kubernetes.**

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


Depending on the selected backend (Argo, Airflow, AWS Batch, or AWS Lambda),
configuration details will change, but the API remains the same:
``soopervisor add``, then ``soopervisor export``.
