# Contributing

Thanks for considering contributing to Soopervisor! This document explains how to set up your development environment.

If you get stuck, [open an issue](https://github.com/ploomber/ploomber/issues/new?title=CONTRIBUTING.md%20issue) or reach out to us on [Slack](https://ploomber.io/community/) and we'll happily help you.

## Setup with conda

The easiest way to set up the development environment is via the setup command; you must have `miniconda` installed.

[Click here for miniconda installation details](https://docs.conda.io/en/latest/miniconda.html).

Once you have conda:

```sh
# get the code
git clone https://github.com/ploomber/soopervisor

# invoke is a library we use to manage one-off commands
pip install invoke

# setup development environment
invoke setup
```

Then activate the environment:

```sh
conda activate soopervisor
```

## Checking setup

Make sure everything is working correctly:

```sh
python -c 'import soopervisor; print(soopervisor)'
```

*Note:* the output of the previous command should be the directory where you ran `git clone`; if it's not, try re-activating your conda environment (i.e., `conda activate base`, then `conda activate soopervisor`) If this doesn't work, [open an issue](https://github.com/ploomber/soopervisor/issues/new?title=CONTRIBUTING.md%20issue) or reach out to us on [Slack](https://ploomber.io/community/).

To run tests:

```
invoke test
```

### Viewing the docs/tutorials
You can run this command to show the rst doc in live mode (you can pass a custom port in this example 9999):

```
invoke doc-auto -p 9999
```

In addition you can run this command to see all of the invoke commands available:

```
invoke -l
```

If we want to understand how to use or change one of the tasks for invoke, we can run --help on the specific task:

```
invoke doc-auto --help
```


## Branch name requirement

To prevent double execution of the same CI pipelines, we have chosen to set a limitation to github push event. Only pushes to certain branches will trigger the pipelines. That means if you have turned on github action and want to run workflows in your forked repo, you will need to either make pushes directly to your master branch or branches name strictly following this convention: `dev/{your-branch-name}`.

On the other hand, if you choose not to turn on github action in your own repo and simply run tests locally, you can disregard this information since your pull request from your forked repo to ploomber/ploomber repo will always trigger the pipelines. 


## Locally running GitHub actions

Debugging GitHub actions by commiting, pushing, and then waiting for GitHub to 
run them can be inconvenient because of the clunky workflow and inability to
use debugging tools other than printing to the console

We can use the tool [`act`](https://github.com/nektos/act) to run github 
actions locally in docker containers

Install then run `act` in the root directory. On the first invocation it will
ask for a size. Select medium. `act` will then run actions from the 
`.github/workflows` directory

#### Working with containers

If the tests fail, act will leave the docker images after the action finishes.
These can be inspected by running `docker container list` then running
`docker exec -it CONTAINER_ID bash` where `CONTAINER_ID` is a container id
from `docker container list`

To install packages in the container, first run `apt-get update`. Packages
can be installed normally with apt after

## Submitting code

[Refer to Ploomber's CONTRIBUTING.md Submitting Code section.](https://github.com/ploomber/ploomber/blob/master/CONTRIBUTING.md#submitting-code)

## Maintaining backward compatibility

We follow [scikit-learn's guidelines](https://scikit-learn.org/stable/developers/contributing.html#maintaining-backwards-compatibility).
