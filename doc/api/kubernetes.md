# Kubernetes

Configuration schema for Kubernetes.

## Example

```yaml
k8s-config:
  exclude: [my-venv/]
  repository: my-docker.repository.io/some-name
  mounted_volumes:
    - name: shared-folder
      spec:
        hostPath:
          path: /host
```

The above `soopervisor.yaml`, translates into the following Argo spec:

```yaml
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
```

## Schema


### `_class_ soopervisor.abc.AbstractConfig()`
Abstract class for configuration objects

**Parameters:**

  * **preset** (*str*) – The preset to use, this determines certain settings and is
  backend-specific


### `_class_ soopervisor.argo.config.ArgoConfig()`
Configuration for exporting to Argo

**Parameters:**

  * **repository** (*str*) – Repository for uploading the Docker image.
  ```{important}
  If `repository` is `null`, it sets the `imagePullPolicy` in the generated spec to `Never`.
  ```
  * **mounted_volumes** (*list*, *optional*) – List of volumes to mount on each Pod, described with the
  `ArgoMountedVolumes` schema.



### `_class_ soopervisor.argo.config.ArgoMountedVolume()`
Volume to mount in the Pod at `/mnt/{name}`

**Parameters:**

  * **name** (*str*) – Volume’s name
  * **sub_path** (*str*, *default=''*) – Sub path from the volume to mount in the Pod (set in
  `volumeMounts[\*].subPath`). Defaults to the volume’s root
  * **spec** (*dict*) – The volume spec, passed directly to the output spec.
  e.g: `{'persistentVolumeClaim': {'claimName': 'someName'}}`
