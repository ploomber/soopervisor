# Soopervisor

Soopervisor runs [Ploomber](https://github.com/ploomber/ploomber) pipelines
for batch processing (large-scale training or batch serving) or online
inference.

```sh
pip install soopervisor
```

Watch our presentation at EuroPython 2021: [Develop and Deploy a Machine Learning Pipeline in 30 Minutes With Ploomber](https://youtu.be/O8tqiCkIWPs).

# Supported platforms


* Batch serving and large-scale training:
    * [Airflow](tutorials/airflow.md)
    * [Argo/Kubernetes](tutorials/kubernetes.md)
    * [AWS Batch](tutorials/aws-batch.md)
    * [Kubeflow](tutorials/kubeflow.md)
    * [SLURM](tutorials/slurm.md)


* Online inference:
    * [AWS Lambda](tutorials/aws-lambda.md)

# From notebook to a production pipeline

We also have [an example](tutorials/workflow.md) that shows how to use our ecosystem of tools to go **from a monolithic notebook to a pipeline deployed in Kubernetes.**

# Standard layout

Soopervisor expects your Ploomber project to be in the standard project
layout, which requires the following:

## Dependencies file


* `requirements.lock.txt`: `pip` dependencies file

```{tip}
You can generate it with pip `freeze > requirements.lock.txt`
```

OR


* `environment.lock.yml`: [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually) with pinned dependencies

```{tip}
You can generate it with pip `conda env export --no-build --file environment.lock.yml`
```

If the list of packages required for your project is a long one and can possibly cause
dependency conflicts, you may also split the required packages across different dependency files.

Example: If you have tasks get, fit-0, fit-1, plot then you may declare two dependency files :
`requirements.lock.txt` / `environment.lock.yml` (which would be specific to tasks get and plot), and `requirements.fit-__.lock.txt` / `environment.fit-__.lock.yml` (which will be specific for tasks fit-0 and fit-1).

## Pipeline declaration

A `pipeline.yaml` file in the current working directory
(or in `src/{package-name}/pipeline.yaml` if your project is a Python
package).

```{note}
If your project is a package (i.e., it has a `src/` directory, a
`setup.py` file is also required.
```

## Scaffolding standard layout

The fastest way to get started is to scaffold a new project:

```sh
# install ploomber
pip install ploomber

# scaffold project
ploomber scaffold

# or to use conda (instead of pip)
ploomber scaffold --conda

# or to use the package structure
ploomber scaffold --package

# or to use conda and the package structure
ploomber scaffold --conda --package
```

Then, configure the development environment:

```sh
# move to your project's root folder
cd {project-name}

# configure dev environment
ploomber install
```

```{note}
`ploomber install` automatically generates the
`environment.lock.yml` or `requirements.lock.txt` file. If you prefer so,
you may skip `ploomber install` and create the lock files yourself.
```

# Usage

Say that you want to train multiple models in a Kubernetes
cluster, you may create a new target environment to execute your pipeline
using Argo Workflows:

```sh
soopervisor add training --backend argo-workflows
```

After filling in some basic configuration settings, export the pipeline with:

```sh
soopervisor export training
```

Soopervisor will take care of packaging your code and submitting it for
execution. Using Argo Workflows will create a Docker image, upload it to
the configured registry, generate an Argo’s YAML spec, and submit the workflow.

Depending on the selected backend (Argo, Airflow, AWS Batch, or AWS Lambda),
configuration details will change, but the API remains the same:
`soopervisor add`, then `soopervisor export`.
