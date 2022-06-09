CHANGELOG
=========

0.8 (2022-06-09)
----------------
* Dropping support for Python 3.6
* Adds ``task_resources`` to AWS Batch
* AWS Batch exporter now generates a unique job definition name on each submission
* Adds ``--lazy`` option to ``soopervisor export``
* Pass custom arguments to ``docker build`` with environment variable ``DOCKER_ARGS``

0.7.2 (2022-02-14)
------------------
* Fixes an error that caused ``soopervisor export`` to fail due to non-serializable object

0.7.1 (2022-02-13)
------------------
**Important:** We detected a problem with this release when running ``soopervisor export``. Please use ``0.7.2``

* Fixes error that caused docker image building to fail if the repository didn't have a version

0.7 (2022-01-31)
----------------

**Important:** We detected a problem with this release when running ``soopervisor export``. Please use ``0.7.2``

* Improves CLI documentation
* Adds ``--git-ignore`` to documentation
* Various documentation improvements
* Changes short version of ``--until-build`` to ``-u``
* Adds "Task Communication" user guide
* Display warnings if passing CLI options that do not apply to SLURM
* SLURM exporter raises error if ``sbatch`` isn't installed
* Showing a warning if source dist is >5MB  (#53)
* ``soopervisor add`` adds a default ``exclude`` value by extracting product paths from ``pipeline.yaml``
* Copying user settings when generating the Docker image
* Experimental Kubeflow integration
* Airflow integration allows to choose between ``BashOperator``, ``KubernetesPodOperator``, and ``DockerOperator`` using ``--preset``
* Many modules and test cases re-written for better code quality and maintainability

0.6.1 (2022-01-16)
------------------
* Fixes output message after exporting to Argo
* Adds flag to ``source.copy`` to ignore git
* ``soopervisor export`` raises and error if ``git`` isn't tracking any files
* Adds ``--git-ignore`` to ``soopervisor export``

0.6 (2022-01-04)
----------------
* Adds support for SLURM
* ``AirflowExporter`` uses ``KubernetesPodOperator`` by default (#33)
* Simplified Airflow and Argo/k8s tutorials

0.5.2 (2022-01-02)
------------------
* Clearer error message when pending ``git commit``
* Clearer error message when the user does not change docker repository default value (#29)
* Argo spec sets ``imagePullPolicy`` to ``Never`` if repository is ``null``
* Documents Kubernetes/Argo configuration schema
* General documentation improvements

0.5.1 (2021-07-26)
------------------
* Better error message when lock files do not exist
* Documentation note on when using shared disks (must pass ``--skip-tests``)
* Adds ``build`` as a dependency
* Check for lock files before creating ``soopervisor.yaml``
* Fixes ``docker.build`` issue that caused a ``pipeline.yaml`` to be used even when the environment required one with another name
* Fixes error that caused AWS batch args to be passed as a single str

0.5 (2021-07-09)
----------------
* load_tasks tries to initialize a spec matching the target env name (e.g., ``training`` target looks for ``pipeline.train.yaml``
* Compatibility fixes with Ploomber (requires >=0.12.1)
* Fixes an error that caused Dockerfile to include a line to install project as a package even if there was no ``setup.py`` file

0.4.2 (2021-06-04)
------------------
* Adds ``exclude`` to ignore files/directories from docker image
* Adds user guide section to documentation

0.4.1 (2021-05-31)
------------------
* Adds ``--mode`` option to ``soopervisor export``
* Batch export stops if there are no tasks to execute
* Adds ``--skip-tests`` option to skip tests before submitting

0.4 (2021-05-22)
----------------

**Important**: Soopervisor was re-written. Some modules were deprecated and the
API changed. This new architecture allows us to greatly simplify user experience
and easily incorporate more platforms in the future.

* New CLI
* New documentation
* New (simplified) ``soopervisor.yaml`` configuration schema
* Support for non-packaged projects (i.e., the ones without a ``setup.py`` file)
* Support for AWS Batch
* Support for AWS Lambda
* Argo Workflows integration builds a docker image
* Airflow integration produces a DAG with ``DockerOperator`` tasks
* Deprecates ``build`` module
* Deprecates ``script`` module
* Deprecates Box integration


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
