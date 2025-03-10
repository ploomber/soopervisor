**Important:** *This project is no longer maintained.*

Soopervisor
-----------

.. image:: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI/badge.svg
   :alt: CI badge

.. image:: https://github.com/ploomber/soopervisor/workflows/CI%20macOS/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI%20macOS/badge.svg
   :alt: CI macOS badge

.. image:: https://github.com/ploomber/soopervisor/workflows/CI%20Windows/badge.svg
   :target: https://github.com/ploomber/soopervisor/workflows/CI%20Windows/badge.svg
   :alt: CI Windows badge

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black


*Tip: Deploy AI apps for free on* `Ploomber Cloud! <https://ploomber.io/?utm_medium=github&utm_source=soopervisor>`_


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


About Ploomber
==============

Ploomber is a big community of data enthusiasts pushing the boundaries of Data Science and Machine Learning tooling.

Whatever your skillset is, you can contribute to our mission. So whether you're a beginner or an experienced professional, you're welcome to join us on this journey!

`Click here to know how you can contribute to Ploomber. <https://github.com/ploomber/contributing/blob/main/README.md>`_
