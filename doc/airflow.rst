Running in Airfow
=================

**Note:** This feature is in beta, if you are interested in being a beta tester, please open an issue in the repository

Maintaining a pipeline running in production is hard, and there are tools
dedicated to that. The most widely used is Apache Airflow. Similarly to
Ploomber, it allows you to write pipelines as DAGs.

The main difference between Ploomber and Airflow is that Ploomber focuses
on providing an interactive development experience, you can write your tasks
as simple Python functions, Jupyter notebooks, SQL scripts or even R scripts,
and Ploomber will take care of converting the collection of functions/scripts
to a pipeline, while still offering you integration with Jupyter to develop
your pipeline interactively.

Airflow is a general-purpose tool aimed to cover more scenarios but it lacks
of an interactive development experience that make us more productive when
analyzing data.

However, we can still leverage Airflow's production-grade scheduler to run our
Ploomber pipelines and get the best of both worlds: a great development
experience and a reliable production scheduler.


Step 1: Parametrizing your pipeline
-----------------------------------

Say you are developing a pipeline, you might choose a folder to save all
outputs (such as ``/data/project/output``. When you deploy to Airflow, it is
unlikely that you have the same filesystem, so you might choose a different
folder (say ``/airflow-data/project/output``). How do you deal with these two
configurations?

Ploomber provides a clean way of achieving this using parametrization
(https://ploomber.readthedocs.io/en/stable/user-guide/parametrized.html), the
basic idea is that you can parametrize where your pipeline saves its output.

To achieve this, Soopervisor looks for a ``env.airflow.yaml`` file which is
used to load your pipeline in Airflow. This way you can keep development
and production configurations separated.

One important thing to keep in mind is that when using Airflow, you should not
store pipeline product's inside the project's root folder, because this can
negatively impact Airflow's performance, which continuously scans folders
looking for new pipeline definitions. To prevent this from happening,
Soopervisor analyzes your pipeline during the export process and shows you
an error message if any pipeline task will attempt to save files inside
the project's root folder.


Step 2: Exporting pipeline
--------------------------

Since Airflow uses Python to declare pipelines, Soopervisor has to generate
a Python file that Airflow understands:

.. code-block:: sh

    soopervisor export-airflow --output airflow/


Once the export process finishes, you'll see a new ``airflow/`` folder with
two sub folders ``dag/``, which contains the Airflow DAG definition and
``ploomber/`` which contains your project's source code. To deploy, just move
those directories to your AIRFLOW_HOME.

If you don't pass the ``--output`` parameter, it will export the project to
AIRFLOW_HOME.


Examples
--------

The sample projects repository contains a few example pipelines that can be
exported to Airflow:


.. code-block:: sh

    git clone https://github.com/ploomber/projects
    cd setup-airflow

    # configure environment
    # if you don't have conda, you can "pip install" the dependencies
    conda env create --file environment.yml
    conda activate setup-airflow

    # init airflow database
    airflow initdb

    # export a few projects
    cd ../ml-intermediate
    soopervisor export-airflow

    cd ../etl
    soopervisor export-airflow

    # initialize airflow
    cd ../setup-airflow
    # shortcut to start airflow and the scheduler (see Procfile for details)
    honcho start


Airflow should start running: http://localhost:8080/

You should see the exported ``ml-intermediate`` and ``etl`` projects as DAGs.


Generated Airflow DAG
---------------------

The exported Airflow DAG has the same structure as the Ploomber DAG and it
generates tasks using ``BashOperator``.


Customizing Airflow output DAG
------------------------------

[WIP]
