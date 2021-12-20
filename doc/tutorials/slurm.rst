Slurm
=====

Pre-requisites
--------------

* ``conda`` `See instructions here <https://docs.conda.io/en/latest/miniconda.html>`_
* `docker and docker-compose <https://docs.docker.com/get-docker/>`_
* `git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
* Install Ploomber with ``pip install ploomber``


Setting up the project
----------------------

.. note:: These instructions are based on `this article <https://medium.com/analytics-vidhya/slurm-cluster-with-docker-9f242deee601>`_.

First, let's create a SLURM cluster for testing.

Create the following ``docker-compose.yml`` file:

.. code-block:: yml

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

Connect to the cluster:

.. code-block:: sh

    docker compose exec slurmjupyter /bin/bash


Configure the environment:

.. code-block:: sh

    # install miniconda (to get a Python environment ready, not needed if 
    # there's already a Python environment up and running)
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash ~/Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
    
    # start conda
    eval "$($HOME/miniconda/bin/conda shell.bash hook)"
    
    # install ploomber and soopervisor in the base environment
    pip install ploomber soopervisor
    pip install git+https://github.com/ploomber/soopervisor@slurm
    
    # download sample pipeline to example/
    ploomber examples -n templates/ml-basic -o example
    cd example

    # add environment
    soopervisor add training --backend slurm
    
    # create the project's virtual env
    python -m venv myproj
    source myproj/bin/activate
    pip install -r requirements.txt

   # submit jobs
   soopervisor export training


Note: since we need to load the dag to define the task's status, the environment
must have all dependencies if there are functions tasks
Note: slurm should not have the docker image arguments when running "soopervisor export"
Note: define a custom config, include/exclude are not relevant for SLURM config

monitor frmo localhost


see example/output

.. code-block:: sh

Stop the cluster:

.. code-block:: sh

     docker-compose stop

