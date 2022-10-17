# Airflow

```{note}
This is a quick reference. For a full
tutorial, [click here.](../tutorials/airflow.md)
```

## Step 1: Add target environment

```{tip}
To get a sample pipeline to try this out, [see this](https://docs.ploomber.io/en/latest/user-guide/templates.html#downloading-a-template).
```

### `KubernetesPodOperator`

```sh
# add a target environment named 'airflow' (uses KubernetesPodOperator)
soopervisor add airflow --backend airflow
```

```{note}
Using the `--preset` option requires `soopervisor>=0.7`
```

```sh
# add a target environment named 'airflow-k8s' (uses KubernetesPodOperator)
soopervisor add airflow-k8s --backend airflow --preset kubernetes
```

### `BashOperator`

```{important}
If using `--preset bash`, the `BashOperator` tasks will use `ploomber` CLI to execute your pipeline. Edit the `cwd` argument in `BashOperator` so your DAG runs in a directory where it can import your project's `pipeline.yaml` and source code.
```

```sh
# add a target environment named 'airflow-bash' (uses BashOperator)
soopervisor add airflow-bash --backend airflow --preset bash
```

### `DockerOperator`

```{important}
Due to a [bug in the DockerOperator](https://github.com/apache/airflow/issues/13487), we must set `enable_xcom_pickling = True` in `airflow.cfg` file. By default, this file is located at `~/airflow/airflow.cfg`.
```

```sh
# add a target environment named 'airflow-docker' (uses DockerOperator)
soopervisor add airflow-docker --backend airflow --preset docker
```

## Step 2: Generate Airflow DAG

```sh
# export target environment named 'airflow'
soopervisor export airflow
```

```{important}
For your pipeline to run successfully, tasks must write their outputs to a common location. You can do this either by creating a shared disk or by adding a storage client. [Click here to learn more.](../user-guide/task-comm)
```
