Slurm
=====

.. tip:: **Got questions?** Reach out to us on `Slack <https://ploomber.io/community/>`_.

This tutorial shows you how to export a Ploomber pipeline to `SLURM <https://slurm.schedmd.com/documentation.html>`_.

If you encounter any issues with this
tutorial, `let us know <https://github.com/ploomber/soopervisor/issues/new?title=SLURM%20tutorial%20problem>`_.

Pre-requisites
--------------

.. important::

    This integration requires ploomber 0.13.7 or higher and soopervisor 0.6
    or higher (To upgrade: ``pip install ploomber soopervisor --upgrade``)

* `docker and docker-compose <https://docs.docker.com/get-docker/>`_


Setting up the project
----------------------

.. note:: These instructions are based on `this article <https://medium.com/analytics-vidhya/slurm-cluster-with-docker-9f242deee601>`_.

First, let's create a SLURM cluster for testing. Create the following ``docker-compose.yml`` file:

.. code-block:: yaml

    services:
      slurmjupyter:
            image: rancavil/slurm-jupyter:19.05.5-1
            hostname: slurmjupyter
            user: admin
            volumes:
                    - shared-vol:/home/admin
            ports:
                    - 8888:8888
      slurmmaster:
            image: rancavil/slurm-master:19.05.5-1
            hostname: slurmmaster
            user: admin
            volumes:
                    - shared-vol:/home/admin
            ports:
                    - 6817:6817
                    - 6818:6818
                    - 6819:6819
      slurmnode1:
            image: rancavil/slurm-node:19.05.5-1
            hostname: slurmnode1
            user: admin
            volumes:
                    - shared-vol:/home/admin
            environment:
                    - SLURM_NODENAME=slurmnode1
            links:
                    - slurmmaster
      slurmnode2:
            image: rancavil/slurm-node:19.05.5-1
            hostname: slurmnode2
            user: admin
            volumes:
                    - shared-vol:/home/admin
            environment:
                    - SLURM_NODENAME=slurmnode2
            links:
                    - slurmmaster
      slurmnode3:
            image: rancavil/slurm-node:19.05.5-1
            hostname: slurmnode3
            user: admin
            volumes:
                    - shared-vol:/home/admin
            environment:
                    - SLURM_NODENAME=slurmnode3
            links:
                    - slurmmaster
    volumes:
            shared-vol:


Now, start the cluster:


.. code-block:: sh

    docker-compose up -d

.. important::

    Ensure you're running a recent version of ``docker-compose``, older
    versions may throw an error like this: 

    .. code-block:: console

        Unsupported config option for volumes: 'shared-vol'
        Unsupported config option for services: 'slurmmaster'


.. tip::

    Once the cluster is up, go `http://localhost:8888 <http://localhost:8888>`_
    to open JupyterLab, where you can edit files, open terminals, and monitor
    Slurm jobs (Click on Slurm Queue under HPC Tools in the Launcher menu) from
    your browser.


Let's connect to the cluster to submit the jobs:

.. code-block:: sh

    docker-compose exec slurmjupyter /bin/bash


Configure the environment:

.. code-block:: sh

    # Install miniconda (to get a Python environment ready, not needed if
    # There's already a Python environment up and running)
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash ~/Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
    
    # Init conda
    eval "$($HOME/miniconda/bin/conda shell.bash hook)"

    # Create and activate env
    conda env create --name myenv
    conda activate myenv

    # install ploomber and soopervisor in the base environment
    pip install ploomber soopervisor
    
    # Download sample pipeline to example/
    ploomber examples -n templates/ml-basic -o example
    cd example

    # Install project dependencies
    pip install -r requirements.txt

    # Register a soopervisor environment with the SLURM backend
    soopervisor add cluster --backend slurm


The ``soopervisor add`` creates a ``cluster/`` directory with a
``template.sh`` file, this is a template that Soopervisor uses to submit
the tasks in your pipeline. If should contain the placeholders
``{{name}}``, and ``{{command}}``, which Soopervisor will replace by the
task name and the command to execute such a task, respectively. You can
customize it to suit your needs.

For example, since we want the tasks to run in the ``conda`` environment
we created, edit the ``template.sh`` so it looks like this:

.. code-block:: sh

    #!/bin/bash
    #SBATCH --job-name={{name}}
    #SBATCH --output=result.out
    #

    # Activate myenv
    conda activate myenv
    srun {{command}}

We can now submit the tasks:


.. code-block:: sh

   soopervisor export cluster

Once jobs finish execution, you'll see the outputs in the ``output`` directory.

.. tip::

   If you execute ``soopervisor export cluster``, only tasks whose source code
   has changed will be executed again, to force the execution of all tasks, run
   ``soopervisor export cluster --mode force``


.. note::

    When scheduling jobs, ``soopervisor`` calls the ``sbatch`` command and
    passes the  ``--kill-on-invalid-dep=yes``, this causes tasks to abort if
    any of its dependencies fails. For example, if you have a ``load -> clean``
    pipeline and ``load`` fails, ``clean`` is aborted.


.. important::

    For Ploomber to determine which tasks to schedule, it needs to parse your
    pipeline and check each task's status. **If your pipeline has functions
    as tasks**, the Python environment where you execute ``soopervisor export``
    must have all dependencies required to import those functions. e.g., if a
    function ``train_model`` uses ``sklearn``, then ``sklearn`` must be
    installed. If your pipeline only contains scripts/notebooks, this is not
    required.


Stop the cluster:

.. code-block:: sh

     docker-compose stop

