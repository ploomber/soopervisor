# Motivation

This project aims to develop a CLI that helps people easily integrate
Continuous Integration in their Ploomber-compatible projects.

Ploomber allows users to easily orchestrate pipeline execution but we want
to provide higher reproducibility guarantees.

By defining a standard project layout, users can trigger a full pipeline run
with a single command. When this is implemented using a Github Action or similar
they can effectively implement CI.

## Project layout

A project must contain the following files:

1. `pipeline.yaml` - Defines the pipeline tasks (Required)
2. `environment.yml` - Dependencies to be installed via `conda` (Required)
3. `ploomber-ci.yaml` - (tentative name) customizes execution options (Optional)
4. `setup.py` - To install the project as a package (Optional)

## Executors

Executors take a project layout and run the pipeline to provide better
reproducibility guarantees.

### Local executor

This is the simplest executor, it only requires `conda` to be installed. This
executor just installs dependencies, runs the pipeline and optionally uploads
artifacts to Box.

### Docker executor

The local executor does not provide strong guarantees since it picks up the
local environment. If the project has undeclared dependencies that picks up
from the OS or reads from files that only exist in the current filesystem,
the pipeline won't be fully reproducible.

By fully reproducibly, we mean taking the code (i.e. `git clone ...`), install
dependencies and be able to reproduce the final pipeline result in a clean
machine. This is where the Docker executor comes in.

It runs the pipeline in a Docker container, if the pipeline runs without
execution, we can say that as long as we run the pipeline using the same
Docker image, we should be able to reproduce results.

## Github action

Github actions are a nice way to setup CI workflows. The user would just
have to provide the standard project layout, configure the Github Action
and the pipeline will be running on a continuous basis to verify it runs
as expected.