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

The above ``soopervisor.yaml``, translates into the following Argo spec:

.. code-block:: yaml
  :caption: argo.yaml

    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    spec:
      templates:
        script:
          volumeMounts:
          - mountPath: /mnt/shared-folder
            name: shared-folder
            subPath: ''
          # continues ...
      - dag:
          tasks:
            # continues...
      volumes:
      - hostPath:
          path: /host
        name: shared-folder


Schema
-------

.. autoclass:: soopervisor.abc.AbstractConfig


.. autoclass:: soopervisor.argo.config.ArgoConfig


.. autoclass:: soopervisor.argo.config.ArgoMountedVolume