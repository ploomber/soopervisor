API
===

Soopervisor can be customized by creating a ``soopervisor.yaml`` file in your
project's root directory.

Whether you are exporting to Argo, Airflow or executing locally, the
configuration schema remains mostly the same. See ``Base settings`` for schema
description.

For extra options when exporting to Argo or Airflow, see the corresponding
section.

When executing locally, locally, only ``Base settings`` apply.

.. toctree::
   :maxdepth: 2

   base
   argo
   airflow