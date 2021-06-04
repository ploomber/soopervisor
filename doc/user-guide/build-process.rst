Docker building process
========================

Installing dependencies
-----------------------

To install dependencies in the Docker image, Soopervisor looks for a
``requirements.lock.txt`` (if using pip) or an ``environment.lock.yml``
(if using conda). Although not strictly enforced, such files should contain
specific versions of each dependency so that breaking changes from any
dependency do not break the pipeline. For example, if your project uses
``ploomber``, ``pandas``, and ``scikit-learn``; your dependencies may look like
this:

.. tab:: requirements.txt

    .. code-block:: txt

        ploomber
        pandas
        scikit-learn

.. tab:: environment.yml

    .. code-block:: yaml

        dependencies:
          - ploomber
          - pandas
          - scikit-learn

The ``lock`` files generated from such files look like this:

.. tab:: requirements.lock.txt

    .. code-block:: txt

        ploomber==0.11
        pandas==1.2.4
        scikit-learn==0.24.2
        # many other lines...

.. tab:: environment.lock.yml
 
    .. code-block:: yaml

        dependencies:
          - ploomber==0.11
          - pandas==1.2.4
          - scikit-learn==0.24.2
          # many other lines...

You can generate such files with the following commands:

.. tab:: requirements.lock.txt

    .. code-block:: sh

        pip freeze > requirements.lock.txt

.. tab:: environment.lock.yml
 
    .. code-block:: sh

        conda env export --no-build --file environment.lock.yml


.. tip::

    If you use ``ploomber install``, ``lock`` files are automatically
    generated.

Included files
--------------

To export to any of the supported platforms, Soopervisor creates a Docker image
from your project. In most cases, there are files in your project that you want
to exclude from the Docker image to reduce its size. Common examples are:
virtual environments, data files, or exploratory notebooks.

The process to determine which files to include changes if your project isn't
a package (i.e., there isn't a ``setup.py`` file) file or it is a package.


Non-packaged projects
*********************

If your project isn't a package and you're using git,  Soopervisor copies every
file tracked by your repository. To see the list of currently tracked
files, run the following command:

.. code-block:: sh

    git ls-tree -r HEAD --name-only

This means that you can control what file goes into the Docker image by changing
your ``.gitignore`` file. If there are git tracked that you want to
exclude, use the ``exclude`` key in ``soopervisor.yaml``


.. code-block:: yaml

    some-target:
        exclude:
            - file-to-exclude.txt

.. note::
    
    If you're not using git, all files are copied into the Docker image by
    default. You can control what to exclude using the ``exclude`` key.

If there are files that git ignores but you want to include, use the
``include`` key:

.. code-block:: yaml

    some-target:
        include:
            - file-to-include.txt

.. tip::

    It's recommended that you use ``.gitignore`` to control which files
    to exclude. The ``include`` and ``exclude`` keys in ``soopervisor.yaml``
    should only be used to list a few particular files.

Packaged projects
*****************

If your project is a package  (i.e., it has a ``setup.py`` file), a
`source distribution <https://packaging.python.org/glossary/#term-Source-Distribution-or-sdist>`_
is generated and copied into the Docker image. This implies that the process to
control which files are included is the same used to control which files
to include in a source distribution. Unfortunately, there is more than one way
to do this. The most reliable way is to use a ``MANIFEST.in`` file,
`click here <https://packaging.python.org/guides/using-manifest-in/>`_ to learn
more.

.. tip::

    You can use ``ploomber scaffold --package`` to quickly generate a
    pre-configured base packaged project. You can then modify the
    ``MANIFEST.in`` file to customize your build.
