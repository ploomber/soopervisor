Continuous Integration
======================

Since Soopervisor takes care of installing the environemnt and running the
pipeline, you can use it to automate pipeline execution on every push.

We actually use Soopervisor to test `Ploomber's examples <https://github.com/ploomber/projects/blob/master/.github/workflows/ci.yml>`_,
if you take a look at the file in the link you'll notice that testing the examples takes just two lines of code:

.. code-block:: sh

   pip install soopervisor
   soopervisor build