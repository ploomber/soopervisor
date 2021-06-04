Non-packaged vs Packaged
========================

Soopervisor supports two types of projects: non-packaged and packaged.

Non-packaged
------------

Non-packaged are simpler projects that require fewer configuration files. They
only need a ``pipeline.yaml`` file to be valid. Non-packaged projects are a
good option for small projects. To create one:


.. code:: sh

    # create a base non-packaged project
    ploomber scaffold


Packaged
--------

Packaged projects have more structured and require more configuration files.
The main advantage is they allow you to organize your work better.

For example, if you have some Python modules that you reuse in several files,
you must to modify your ``PYTHONPATH`` or ``sys.path`` to ensure that such
modules are importable. If your project is packaged, this isn't necessary,
since you can install your project with pip:

.. code:: sh

    pip install --editable path/to/myproject

After installation, you can import modules from your project anywhere in a
Python session, notebook, or other modules inside your project, making it
simpler to create modular code.

To create a base package project:

.. code:: sh

    # create a base packaged project
    ploomber scaffold --package