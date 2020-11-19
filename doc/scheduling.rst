Scheduling
==========

Often, pipelines are required to run periodically. Since Soopervisor handles
virtual environment creation, pipeline execution and artifact storage, it
makes it easy to do so.

This sections shows a few approaches to run pipelines on a schedule. Before you
go to the examples, make sure you have a copy of the sample projects:

.. code-block:: sh

    git clone https://github.com/ploomber/projects

Cron
----

The simplest deployment approach is to use cron. Assume conda is installed at
``$HOME/miniconda3`` and cloned the projects at ``$HOME/projects``, if your
setup differs, update paths accordingly.

Create the following script in your home directory, and call it ``pipeline.sh``.

.. code-block:: sh

    set -e
    echo Running...
    # print date
    date
    source $HOME/miniconda3/etc/profile.d/conda.sh
    conda activate
    cd $HOME/projects/spec-api-python
    soopervisor build


Then edit your crontab (by running the ``crontab -e`` command):

.. code-block:: sh

    SHELL=/bin/bash
    LANG=en_US.UTF-8
    LC_ALL=en_US.UTF-8

    # run the pipeline every hour, save logs to cron.log
    0 * * * * bash pipeline.sh >> cron.log 2>&1


The sample pipeline will run every hour, saving its output
in the ``$HOME/projects/spec-api-python/runs/{{now}}`` directory, where
``{{now}}`` will be replaced by the timestamp at execution time.


Github Actions
--------------

If you don't have access to a machine that is turned on all the time, you can
use Github Actions to schedule your pipelines.

.. code-block:: yaml

    name: sheduled-pipeline
    on:
      schedule:
        # run every hour
        - cron: '0 * * * *'


    jobs:
      run-pipeline:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
          - uses: actions/setup-python@v2
            with:
              python-version: 3.8
          - run: |
            cd path/to/your/pipeline
            pip install soopervisor
            soopervisor build

See `the documentation <https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-syntax-for-github-actions>`_ for more details.


Argo
----

If you have access to a Kubernetes cluster and can install (or already have
installed) Argo, you can also use it for scheduling. To know
more see :doc:`kubernetes/`

Airflow
-------

If you have access to an Airflow server, you can also schedule pipelines
there. To know more see :doc:`airflow/`