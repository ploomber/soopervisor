# Task communication

Since `soopervisor` executes tasks in isolated environments, you must provide
a way to pass the output files of each task to upcoming tasks that use them as
inputs.

There are two ways of doing so: either mount a shared disk on all containers,
or configure a `File` client to use remote storage; we describe both options
in the next sections.

## Shared disk


````{tab-set}
```{tab-item} K8s/Argo

If using K8s/Argo, you can mount a volume on each pod by adding some configuration to your soopervisor.yaml file. Refer to the [Kubernetes](../api/kubernetes) configuration schema documentation for details.

Note that the configuration flexibility is limited; if you need a more flexible approach, you can generate the Argo YAML Spec (by running the `soopervisor export` command), and then edit the generated spec to suit your needs (the spec is generated in `{name}/argo.yaml`, where `{name}` is the name of your target environment).
```

```{tab-item} Airflow

When using Airflow, the `soopervisor` add generates an `output.py` file with the Airflow DAG, you can edit this file to configure a shared disk and execute soopervisor export afterwards. The [Airflow](../tutorials/airflow) tutorial shows how to do this, you can see the `.py` file that the tutorial uses [here](https://github.com/ploomber/soopervisor/blob/master/tutorials/airflow/ml-intermediate.py).
```

```{tab-item} AWS Batch

To execute pipelines in AWS Batch, you must create a [compute environment](https://docs.aws.amazon.com/batch/latest/userguide/compute_environments.html), map it to a job queue, and include the job queue name in your `soopervisor.yaml` file. You can configure a shared disk using Amazon EFS, [click here](https://aws.amazon.com/premiumsupport/knowledge-center/batch-mount-efs/) to learn how to configure EFS in your compute environment.
```

```{tab-item} SLURM

If running on SLURM, sharing a disk depends on your cluster configuration, so ensure you can mount a disk in all nodes and that your pipeline writes their outputs in the shared disk.
```
````

```{important}
If using a shared disk, execute `soopervisor export` with the `--skip-tests` flag, otherwise Soopervisor will raise an error if your pipeline does not have a `File` client configured.
```


## Using remote storage

As an alternative, you can configure a `File` client to ensure each task
has their input files before execution. We currently support Amazon S3 and
Google Cloud Storage.

To configure a client, add the following to your `pipeline.yaml` file:

```yaml
# configure a client
clients:
    # note the capital F
    File: clients.get
tasks:
    # content continues...
```

Then, create a `clients.py` file (in the same directory as your
`pipeline.yaml`) and declare a `get` function that returns a `File`
client instance:


`````{tab-set}
````{tab-item} Amazon S3

  ```python
  from ploomber.clients import S3Client

  def get():
      return S3Client(bucket_name='YOUR-BUCKET-NAME',
                      parent='PARENT-FOLDER-IN-BUCKET',
                      json_credentials_path='credentials.json')
  ```

  [Click here to see the S3Client documentation.](https://docs.ploomber.io/en/latest/api/_modules/clients/ploomber.clients.S3Client.html)
````

````{tab-item} GCloud

  ```python
  from ploomber.clients import GCloudStorageClient

  def get():
      return GCloudStorageClient(bucket_name='YOUR-BUCKET-NAME',
                                 parent='PARENT-FOLDER-IN-BUCKET',
                                 json_credentials_path='credentials.json')
  ```
  [Click here to see the GCloudStorageClient documentation.](https://docs.ploomber.io/en/latest/api/_modules/clients/ploomber.clients.GCloudStorageClient.html)
````
`````

Next, create a `credentials.json` (in the same directory as your
`pipeline.yaml`) with your authentication information. The
file should look like this:


`````{tab-set}
````{tab-item} S3

  ```json
  {
      "aws_access_key_id": "YOUR-ACCESS-KEY-ID",
      "aws_secret_access_key": "YOU-SECRET-ACCESS-KEY"
  }
  ```
````

````{tab-item} GCloud

  ```json
  {
      "type": "service_account",
      "project_id": "project-id",
      "private_key_id": "private-key-id",
      "private_key": "private-key",
      "client_email": "client-email",
      "client_id": "client-id",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account.iam.gserviceaccount.com"
  }
  ```
````
`````

**Note:** If you’re using a Docker-based exporter (K8s/Argo, Airflow, or
AWS Batch),you must ensure that your `credentials.json` file is included in
your Docker image. You can ensure this by adding the following to your
`soopervisor.yaml`

The `soopervisor.yaml` file:
```yaml
some-name:
    # tell soopervisor to include the credentials.json file
    include: [credentials.json]
    # continues
```

You can check your local configuration by loading your pipeline using
`ploomber status`. If you see a table listing your tasks, it means the
client has been configured successfully.

Furthermore, when executing the `soopervisor export` command and using
a Docker-based exporter (K8s/Argo, Airflow, and AWS Batch), Soopervisor
will check that the `File` client in the Docker image is correctly configured
by trying to establish a connection with your credentials to the remote storage.
