# AWS Batch

Configuration schema for AWS Batch.

## Basic example

```yaml
training:
    backend: aws-batch
    repository: your-repository-url/name
    job_queue: your-job-queue
    region_name: your-region-name
    container_properties:
        memory: 16384
        vcpus: 8
```

## Custom resources

```{note}
**Versionadded:** New in version 0.8: Custom resources via `task_resources`
```

To set custom resources per task:

```yaml
training:
    backend: aws-batch
    repository: your-repository-url/name
    job_queue: your-job-queue
    region_name: your-region-name
    # this will the the default
    container_properties:
        memory: 16384
        vcpus: 8
        gpu: none
    task_resources:
        # replace task_name with the actual task name
        # in your pipeline
        task_name:
            memory: 16384
            vcpus: 4
            gpu: 1
        # you can also use wildcards, to match all tasks with the
        # fit- prefix
       fit-*:
            memory: 16384
            vcpus: 4
            gpu: 1
```

## Schema

### `_class_ soopervisor.abc.AbstractConfig()`
Abstract class for configuration objects

**Parameters:**

* **preset** (*str*) – The preset to use, this determines certain settings and is
backend-specific



### `_class_ soopervisor.aws.config.AWSBatchConfig()`

### `_class_ soopervisor.aws.config.TaskResource()`
