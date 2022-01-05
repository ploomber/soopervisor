Kubernetes
==========

Configuration schema for Kubernetes.

Example
-------

.. code-block:: yaml
    :caption: soopervisor.yaml

    k8s-config:
      exclude: [my-venv/]
      repository: my-docker.repository.io/some-name
      mounted_volumes:
        - name: shared-folder
          spec:
            hostPath:
            path: /host


Schema
-------

.. autoclass:: soopervisor.abc.AbstractConfig


.. autoclass:: soopervisor.argo.config.ArgoConfig


.. autoclass:: soopervisor.argo.config.ArgoMountedVolume