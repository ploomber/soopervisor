Export to Airflow
=================

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

Parametrizing your pipeline
---------------------------

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


Exporting pipeline
------------------

Since Airflow uses Python to declare pipelines, Soopervisor has to generate
a Python file that Airflow understands:

.. code-block:: sh

    soopervisor export {path-to-project}


Once the export process finishes, you can move the script to Airlow's
DAG folder (usually located at ``AIRFLOW_HOME/dags/``) and your project's
source code to ``AIRFLOW_HOME/ploomber/``.


Examples
--------

TODO: link to examples
TODO: link to "to-airflow" repository once it's ready


Customizing Airflow output DAG
------------------------------

[WIP]


Configuration
-------------


:doc:`local`

An optional ``soopervisor.yaml`` file allows you to customize the build process.

Configuration for exporting Ploomber projects to Airflow.

It has the same schema as ScriptConfig, with a few restrictions, to make
deployment simpler and changes a few default values that make more sense
for an Airflow deployment.


