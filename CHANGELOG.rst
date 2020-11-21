CHANGELOG
=========

0.2.2 (2020-11-21)
-------------------
* Adds ability to skip dag loading during project validation
* Box uploader imported only if needed
* Exposes option to skip dag loading from the CLI


0.2.1 (2020-11-20)
-------------------
* Adds Airflow DAG export
* Adds Argo/Kubernetes DAG export
* Support for uploading products to Box


0.2 (2020-10-15)
----------------
* Adds ``DockerExecutor``
* Products are saved in a folder with the name of the current commit by default
* Conda environments are created locally in a `.soopervisor/` folder
* Conda environments are cached by default
* Ability to customize arguments to ``ploomber build``

0.1 (2020-08-09)
-----------------

* First release
