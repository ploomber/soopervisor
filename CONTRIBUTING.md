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

## Submitting code

[Refer to Ploomber's CONTRIBUTING.md Submitting Code section.](https://github.com/ploomber/ploomber/blob/master/CONTRIBUTING.md#submitting-code)

## Maintaining backward compatibility

We follow [scikit-learn's guidelines](https://scikit-learn.org/stable/developers/contributing.html#maintaining-backwards-compatibility).
