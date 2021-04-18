CHANGELOG
=========

0.3.4 (2021-04-18)
------------------
* Export projects compatible with `ploomber.OnlineModel` to AWS Lambda
* Allow initialization from empty `soopervisor.yaml`

0.3.3 (2021-03-07)
------------------
* Support to pass extra cli args to ``ploomber task`` (via ``args`` in ``soopervisor.yaml``) when running in Argo and Airflow

0.3.2 (2021-02-13)
------------------
* Adds ``--root`` arg to ``soopervisor export-airflow`` to select an alternative project's root
* Determines default entry point using Ploomber's API to allow automated discovery of ``pipeline.yaml`` in package layouts (e.g. ``src/package/pipeline.yaml``)


0.3.1 (2021-02-11)
------------------
* Changes to the Airflow generated DAG
* Fixes a bug when initializing configuration from projects whose root is not the current directory

0.3 (2021-01-24)
----------------
* ``env.airflow.yaml`` optional when exporting to Airflow (#17)
* Validating exported argo YAML spec
* Output argo YAML spec displays script in literal mode to make it readable
* Fixed extra whitespace in generated script
* Refactors ``ArgoMountedVolume`` to provide flexibility for different types of k8s volumes
* Adds section in the documentation to run examples using minikube
* Adds a few ``echo`` statements to generated script to provide better status feedback


0.2.2 (2020-11-21)
------------------
* Adds ability to skip dag loading during project validation
* Box uploader imported only if needed
* Exposes option to skip dag loading from the CLI


0.2.1 (2020-11-20)
------------------
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
